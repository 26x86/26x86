#!/usr/bin/env python3
"""Validate the portable VMApple/TCG contract without opening guest inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT / "vmapple-tcg-machine-contract.json"
PATCH_ROOT = ROOT.parent.parent / "research" / "venfire" / "patches"
PATCH_SERIES = PATCH_ROOT / "series"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def patch_series() -> list[Path]:
    if not PATCH_SERIES.is_file():
        raise ValueError(f"missing QEMU patch series: {PATCH_SERIES}")
    names = [line.strip() for line in PATCH_SERIES.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not names or len(names) != len(set(names)):
        raise ValueError("QEMU patch series must be nonempty and unique")
    paths = []
    for name in names:
        path = PATCH_ROOT / name
        if Path(name).name != name or path.suffix != ".patch" or not path.is_file():
            raise ValueError(f"invalid QEMU patch series entry: {name}")
        paths.append(path)
    return paths


def validate() -> dict[str, object]:
    document = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if document.get("schema") != "venfire-vmapple-tcg-machine-contract/1":
        raise ValueError("unexpected VMApple TCG contract schema")
    source = document.get("qemu_source")
    if not isinstance(source, dict) or source.get("machine") != "vmapple" or source.get("accelerator") != "tcg":
        raise ValueError("contract must pin the VMApple TCG backend")
    commit = source.get("commit")
    if not isinstance(commit, str) or len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("contract must pin a full lowercase QEMU commit")
    patches = patch_series()
    if source.get("patch_series") != "research/venfire/patches/series":
        raise ValueError("contract patch series path is not repository-owned")
    recorded = source.get("patches")
    expected = [{"path": str(path.relative_to(ROOT.parent.parent)).replace("\\", "/"), "sha256": sha256(path)}
                for path in patches]
    if recorded != expected:
        raise ValueError("contract QEMU patch series digest does not match the repository")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("VMApple TCG contract has no components")
    names: set[str] = set()
    states: dict[str, int] = {}
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("VMApple TCG components must be objects")
        name = component.get("name")
        state = component.get("state")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("VMApple TCG component names must be unique")
        if state not in {"planned", "in-progress", "runtime-tested", "blocked", "awaiting-caller-input"}:
            raise ValueError(f"invalid VMApple TCG state for {name}")
        if state == "blocked" and not isinstance(component.get("known_gap"), str):
            raise ValueError(f"blocked VMApple TCG component lacks known_gap: {name}")
        names.add(name)
        states[state] = states.get(state, 0) + 1
    return {
        "schema": document["schema"],
        "qemu_commit": commit,
        "patch_series": {"path": str(PATCH_SERIES), "patches": expected},
        "component_count": len(components),
        "component_states": states,
        "guest_input_modification": document["guest_input_policy"]["image_modification"],
        "hardware_or_virtualization_framework_required": False,
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        result = validate()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, separators=(",", ":") if args.compact else None))
        return 2
    print(json.dumps(result, separators=(",", ":") if args.compact else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
