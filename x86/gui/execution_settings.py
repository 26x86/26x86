"""Validate a complete GUI choice before atomically publishing its settings."""
import json
import os
from pathlib import Path
import tempfile

from x86.mellow.integration import configuration


def effective(settings):
    try:
        context, deployment, payload, efi = configuration(settings=settings)
    except (ValueError, TypeError) as error:
        # Presentation-only recovery. Native entry points still use configuration
        # directly and reject the stored/environment conflict until corrected.
        from x86.execution import resolve_execution
        try:
            context = resolve_execution(settings=settings)
        except ValueError:
            context = resolve_execution("apple-silicon-sandbox", settings={}, environ={})
        display = context.as_dict()
        display.update(can_native_plan=False, can_native_apply=False,
                       environment_locked="X86_EXECUTION_MODE" in os.environ)
        from x86.paths import Paths
        return {"execution": display, "execution_error": str(error),
                "mellow_deployment": "disabled", "mellow_payload": str(Paths.repo_root() / "payloads/Mellow"),
                "mellow_efi": str(settings.get("mellow_efi") or ""), "native_metal_verified": False}
    return {"execution": context.as_dict(), "mellow_deployment": deployment,
            "mellow_payload": str(payload), "mellow_efi": str(efi or ""),
            "native_metal_verified": False}


def save_choice(store, updates):
    if not isinstance(updates, dict):
        raise ValueError("Settings must be an object")
    allowed = {"execution_mode", "mellow_deployment", "mellow_payload", "mellow_efi",
               "analytics", "verbose_logging"}
    if set(updates) - allowed:
        raise ValueError("Unknown GUI setting")
    current = store.load()
    candidate = {**current, **updates}
    for key in ("mellow_payload", "mellow_efi"):
        if key in candidate and (not isinstance(candidate[key], str) or "\x00" in candidate[key]):
            raise ValueError("Invalid Mellow path")
    for key in ("analytics", "verbose_logging"):
        if key in candidate and type(candidate[key]) is not bool:
            raise ValueError("Boolean setting required")
    for key, env in (("mellow_deployment", "X86_MELLOW_DEPLOYMENT"),
                     ("mellow_payload", "X86_MELLOW_PAYLOAD"), ("mellow_efi", "X86_MELLOW_EFI")):
        if key in updates and env in os.environ and updates[key] != os.environ[env]:
            raise ValueError(env + " locks this process setting")
    context, deployment, payload, efi = configuration(mode=candidate.get("execution_mode"),
        deployment=candidate.get("mellow_deployment"), payload_dir=candidate.get("mellow_payload"),
        efi=candidate.get("mellow_efi"), settings=candidate)
    if deployment != "disabled":
        from x86.mellow.integration import plan
        plan(mode=context.mode.value, deployment=deployment, payload_dir=payload, efi=efi, settings=candidate)
    candidate.update(execution_mode=context.mode.value, mellow_deployment=deployment,
                     mellow_payload=str(payload), mellow_efi=str(efi or ""))
    path = Path(store.config_path)
    if path.is_symlink():
        raise ValueError("Settings symlink rejected")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".26x86-settings-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(candidate, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return candidate
