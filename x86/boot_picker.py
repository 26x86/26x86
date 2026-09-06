"""Fail-closed two-second boot picker policy and input state machine.

The picker is a control-plane component.  It describes which macOS entry the
EFI/VMApple layers may select and records the hot-key event; it does not load
an EFI image, alter an ESP, or claim that macOS booted.  The recovery entry is
deliberately macOS-only and is bound to the iBoot DFU/IPSW policy.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any, Callable

from .iboot_personality import (
    DEFAULT_RECOVERY_IMAGE,
    IBOOT_MACHINE_TYPE,
    MACOS_GUEST_OS,
    validate_iboot_scope,
)


BOOT_DELAY_SECONDS = 2.0
DEFAULT_ALT_KEY = "Alt"
MACOS_ENTRY_ID = "macos"
RECOVERY_ENTRY_ID = "recovery"

_ALT_KEYS = frozenset({"alt", "option", "leftalt", "rightalt", "menu"})
_MOVE_KEYS = {
    "arrowup": -1,
    "up": -1,
    "arrowleft": -1,
    "left": -1,
    "arrowdown": 1,
    "down": 1,
    "arrowright": 1,
    "right": 1,
}


class BootPickerError(ValueError):
    """A picker request is outside the fixed macOS boot/recovery contract."""

    def __init__(self, message: str, *, code: str = "VF_BOOT_PICKER_CONFIG_INVALID") -> None:
        self.code = code
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}


@dataclass(frozen=True)
class BootPickerEntry:
    entry_id: str
    label: str
    kind: str
    target_major: int
    guest_os: str = MACOS_GUEST_OS
    recovery_protocol: str | None = None
    recovery_image_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.entry_id,
            "label": self.label,
            "kind": self.kind,
            "target_major": self.target_major,
            "guest_os": self.guest_os,
            "supported": True,
        }
        if self.recovery_protocol is not None:
            result["recovery_protocol"] = self.recovery_protocol
        if self.recovery_image_name is not None:
            result["recovery_image_name"] = self.recovery_image_name
        return result


def _canonical_key(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(value.strip().casefold().split())


def _canonical_alt_key(value: object) -> str:
    token = _canonical_key(value)
    if token in _ALT_KEYS:
        return DEFAULT_ALT_KEY
    return ""


def _entries(target_major: int, *, recovery_protocol: str,
             recovery_image_name: str) -> tuple[BootPickerEntry, ...]:
    return (
        BootPickerEntry(
            MACOS_ENTRY_ID,
            f"macOS {target_major}",
            "macOS",
            target_major,
        ),
        BootPickerEntry(
            RECOVERY_ENTRY_ID,
            f"macOS Recovery · {recovery_image_name}",
            "Recovery",
            target_major,
            recovery_protocol=recovery_protocol,
            recovery_image_name=recovery_image_name,
        ),
    )


def validate_boot_picker_config(
    *,
    enabled: object = True,
    delay_seconds: object = BOOT_DELAY_SECONDS,
    alt_key: object = DEFAULT_ALT_KEY,
    show_picker_on_alt: object = True,
    target_major: object = 27,
    recovery_enabled: object = True,
    recovery_protocol: object = "DFU/IPSW",
    recovery_image_name: object = DEFAULT_RECOVERY_IMAGE,
) -> dict[str, Any]:
    """Validate the fixed 2-second Alt→picker→macOS Recovery contract."""
    if type(enabled) is not bool:
        raise BootPickerError("BootPicker.Enabled must be a boolean.")
    if not enabled:
        return {
            "enabled": False,
            "delay_seconds": BOOT_DELAY_SECONDS,
            "alt_key": DEFAULT_ALT_KEY,
            "show_picker_on_alt": True,
            "entries": [],
            "recovery_entry_enabled": False,
        }
    if isinstance(delay_seconds, bool) or not isinstance(delay_seconds, (int, float)):
        raise BootPickerError("BootPicker.DelaySeconds must be exactly 2 seconds.")
    if not math.isfinite(float(delay_seconds)) or float(delay_seconds) != BOOT_DELAY_SECONDS:
        raise BootPickerError(
            "BootPicker.DelaySeconds is fixed at 2 seconds.",
            code="VF_BOOT_PICKER_DELAY_INVALID",
        )
    canonical_alt = _canonical_alt_key(alt_key)
    if not canonical_alt:
        raise BootPickerError(
            "BootPicker.AltKey must be Alt or Option.",
            code="VF_BOOT_PICKER_HOTKEY_INVALID",
        )
    if type(show_picker_on_alt) is not bool:
        raise BootPickerError("BootPicker.ShowPickerOnAlt must be a boolean.")
    if type(target_major) is not int or target_major not in (26, 27):
        raise BootPickerError(
            "BootPicker target must be macOS 26 or 27.",
            code="VF_TARGET_SCOPE_VIOLATION",
        )
    if type(recovery_enabled) is not bool or not recovery_enabled:
        raise BootPickerError(
            "BootPicker.RecoveryEntry.Enabled must be true for the Recovery entry.",
            code="VF_RECOVERY_CONFIG_INVALID",
        )
    personality = validate_iboot_scope(
        IBOOT_MACHINE_TYPE,
        MACOS_GUEST_OS,
        recovery_protocol=recovery_protocol,
        recovery_image_name=recovery_image_name,
        recovery_enabled=True,
        target_major=target_major,
    )
    entries = _entries(
        target_major,
        recovery_protocol=personality["recovery"]["protocol"],
        recovery_image_name=personality["recovery"]["image_name"],
    )
    return {
        "enabled": True,
        "delay_seconds": BOOT_DELAY_SECONDS,
        "alt_key": canonical_alt,
        "show_picker_on_alt": show_picker_on_alt,
        "hotkey_action": "show-picker",
        "entries": [entry.to_dict() for entry in entries],
        "recovery_entry_enabled": True,
        "recovery": personality["recovery"],
    }


def default_boot_picker_config(*, target_major: int = 27) -> dict[str, Any]:
    """Return the product default without touching firmware or storage."""
    return validate_boot_picker_config(target_major=target_major)


class BootPickerSession:
    """Deterministic picker session used by EFI/GUI bridges and tests.

    ``now`` is injectable on each operation so tests can prove the exact
    two-second boundary without sleeping.  The production GUI uses monotonic
    time and sends its real DOM key event through :meth:`key_event`.
    """

    def __init__(
        self,
        *,
        target_major: int = 27,
        delay_seconds: float = BOOT_DELAY_SECONDS,
        alt_key: str = DEFAULT_ALT_KEY,
        recovery_protocol: str = "DFU/IPSW",
        recovery_image_name: str = DEFAULT_RECOVERY_IMAGE,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.policy = validate_boot_picker_config(
            delay_seconds=delay_seconds,
            alt_key=alt_key,
            target_major=target_major,
            recovery_protocol=recovery_protocol,
            recovery_image_name=recovery_image_name,
        )
        self.target_major = target_major
        self._clock = clock or time.monotonic
        self._entries = tuple(
            BootPickerEntry(
                item["id"],
                item["label"],
                item["kind"],
                item["target_major"],
                item["guest_os"],
                item.get("recovery_protocol"),
                item.get("recovery_image_name"),
            )
            for item in self.policy["entries"]
        )
        self._started_at: float | None = None
        self._state = "idle"
        self._selected_index = 0
        self._selection: str | None = None
        self._trigger: str | None = None
        self._events: list[dict[str, Any]] = []

    @property
    def delay_seconds(self) -> float:
        return float(self.policy["delay_seconds"])

    def start(self, *, now: float | None = None) -> dict[str, Any]:
        timestamp = self._clock() if now is None else float(now)
        self._started_at = timestamp
        self._state = "armed"
        self._selected_index = 0
        self._selection = None
        self._trigger = None
        self._events = [{"event": "armed", "at": timestamp}]
        return self.snapshot(now=timestamp)

    def _timestamp(self, now: float | None) -> float:
        return self._clock() if now is None else float(now)

    def _elapsed(self, now: float) -> float:
        if self._started_at is None:
            return 0.0
        return max(0.0, now - self._started_at)

    def _expire(self, now: float) -> None:
        if self._state == "armed" and self._elapsed(now) >= self.delay_seconds:
            self._state = "default"
            self._selection = MACOS_ENTRY_ID
            self._trigger = "timeout"
            self._events.append({"event": "default-selected", "entry": MACOS_ENTRY_ID, "at": now})

    def tick(self, *, now: float | None = None) -> dict[str, Any]:
        timestamp = self._timestamp(now)
        self._expire(timestamp)
        return self.snapshot(now=timestamp)

    def key_event(
        self,
        key: object,
        *,
        pressed: bool = True,
        now: float | None = None,
    ) -> dict[str, Any]:
        timestamp = self._timestamp(now)
        if self._state == "idle":
            raise BootPickerError("BootPicker session is not armed.", code="VF_BOOT_PICKER_NOT_ARMED")
        if not pressed:
            return self.snapshot(now=timestamp)
        token = _canonical_key(key)
        # The hot-key window includes the two-second endpoint.  Check Alt
        # before expiring so an event delivered at exactly 2.000s is retained.
        if (
            self._state == "armed"
            and self.policy["show_picker_on_alt"]
            and token in _ALT_KEYS
            and self._elapsed(timestamp) <= self.delay_seconds
        ):
            self._state = "picker"
            self._trigger = "alt"
            self._events.append({"event": "picker-shown", "key": DEFAULT_ALT_KEY, "at": timestamp})
            return self.snapshot(now=timestamp)
        self._expire(timestamp)
        if self._state != "picker":
            return self.snapshot(now=timestamp)
        if token in _MOVE_KEYS:
            self._selected_index = (self._selected_index + _MOVE_KEYS[token]) % len(self._entries)
            self._events.append({
                "event": "selection-moved",
                "entry": self._entries[self._selected_index].entry_id,
                "at": timestamp,
            })
        elif token in {"enter", "return"}:
            self._selection = self._entries[self._selected_index].entry_id
            self._state = "selected"
            self._trigger = "alt-enter"
            self._events.append({"event": "entry-selected", "entry": self._selection, "at": timestamp})
        elif token in {"escape", "esc"}:
            self._selection = MACOS_ENTRY_ID
            self._state = "default"
            self._trigger = "escape"
            self._events.append({"event": "picker-cancelled", "entry": MACOS_ENTRY_ID, "at": timestamp})
        return self.snapshot(now=timestamp)

    def select(self, entry_id: object, *, now: float | None = None) -> dict[str, Any]:
        timestamp = self._timestamp(now)
        if self._state != "picker":
            raise BootPickerError(
                "BootPicker entry selection requires the picker to be visible.",
                code="VF_BOOT_PICKER_NOT_VISIBLE",
            )
        if not isinstance(entry_id, str) or entry_id not in {entry.entry_id for entry in self._entries}:
            raise BootPickerError(
                "Unknown BootPicker entry.",
                code="VF_BOOT_PICKER_ENTRY_INVALID",
            )
        self._selected_index = next(
            index for index, entry in enumerate(self._entries) if entry.entry_id == entry_id
        )
        self._selection = entry_id
        self._state = "selected"
        self._trigger = "alt-pointer"
        self._events.append({"event": "entry-selected", "entry": entry_id, "at": timestamp})
        return self.snapshot(now=timestamp)

    def snapshot(self, *, now: float | None = None) -> dict[str, Any]:
        timestamp = self._timestamp(now)
        elapsed = self._elapsed(timestamp)
        remaining = max(0.0, self.delay_seconds - elapsed) if self._state == "armed" else 0.0
        selected = self._entries[self._selected_index] if self._entries else None
        return {
            "schema": "26x86.boot-picker/1",
            "machine_type": IBOOT_MACHINE_TYPE,
            "personality": "iBoot",
            "guest_os": MACOS_GUEST_OS,
            "target_major": self.target_major,
            "state": self._state,
            "delay_seconds": self.delay_seconds,
            "remaining_seconds": round(remaining, 3),
            "alt_key": self.policy["alt_key"],
            "picker_visible": self._state == "picker",
            "selected_entry": selected.entry_id if selected else None,
            "selection": self._selection,
            "trigger": self._trigger,
            "entries": [entry.to_dict() for entry in self._entries],
            "recovery": self.policy["recovery"],
            "events": list(self._events),
            "macos_boot_verified": False,
        }


__all__ = [
    "BOOT_DELAY_SECONDS",
    "DEFAULT_ALT_KEY",
    "MACOS_ENTRY_ID",
    "RECOVERY_ENTRY_ID",
    "BootPickerEntry",
    "BootPickerError",
    "BootPickerSession",
    "default_boot_picker_config",
    "validate_boot_picker_config",
]
