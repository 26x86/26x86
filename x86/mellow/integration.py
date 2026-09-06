"""26x86 entry points for Mellow deployment, never a Metal capability claim."""
from __future__ import annotations

import copy
import os
import plistlib
import shutil
from pathlib import Path

from x86.execution import resolve_execution
from x86.settings import SettingsStore

MELLOW_ID = "com.NiSeullent.Mellow"
APPLE_GUID = "7C436110-AB2A-4BBB-A880-FE41995C9F82"
DEPLOYMENTS = ("disabled", "efi", "root-patch")


def configuration(*, mode=None, deployment=None, payload_dir=None, efi=None, settings=None):
    settings = SettingsStore().load() if settings is None else settings
    context = resolve_execution(mode, settings=settings)
    deployment = deployment if deployment is not None else os.environ.get(
        "X86_MELLOW_DEPLOYMENT", settings.get("mellow_deployment", "disabled"))
    if deployment not in DEPLOYMENTS:
        raise ValueError("Unknown Mellow deployment")
    if deployment != "disabled":
        context.require_native_plan()
    from x86.paths import Paths
    return context, deployment, Path(payload_dir or os.environ.get("X86_MELLOW_PAYLOAD") or
        settings.get("mellow_payload") or Paths.repo_root() / "payloads/Mellow"), (
        efi or os.environ.get("X86_MELLOW_EFI") or settings.get("mellow_efi"))


def configure_constants(constants, **options):
    context, deployment, payload, efi = configuration(**options)
    constants.execution_mode = context.mode.value
    constants.mellow_deployment = deployment
    constants.mellow_payload_path = str(payload.resolve())
    constants.mellow_efi_path = str(Path(efi).expanduser().resolve()) if efi else None
    return context


def execution_for(constants):
    # Resolve host facts again at a privileged boundary; cached UI data is not authority.
    return resolve_execution(getattr(constants, "execution_mode", None), settings=SettingsStore().load())


def selected_payload(constants):
    if getattr(constants, "mellow_deployment", "disabled") != "root-patch":
        return None
    context = execution_for(constants)
    context.require_native_plan()
    from .payload import load_payload
    return load_payload(Path(constants.mellow_payload_path), mode=context.mode.value)


def _contained(root, relative):
    if not isinstance(relative, str) or "\\" in relative or ":" in relative or Path(relative).is_absolute():
        raise ValueError("Invalid EFI relative path")
    path = root / relative
    if any(p.exists() and (p.is_symlink() or getattr(p.lstat(), "st_file_attributes", 0) & 0x400)
           for p in (path, *path.parents) if p == root or root in p.parents) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("EFI path escapes its root: " + str(relative))
    return path


def inspect_efi(path):
    root = Path(path).expanduser().resolve()
    if (root / "EFI/OC/config.plist").is_file():
        root /= "EFI"
    config_path = _contained(root, "OC/config.plist")
    config = plistlib.loads(config_path.read_bytes())
    enabled = {}
    mellow_entries = []
    for index, entry in enumerate(config["Kernel"]["Add"]):
        if not entry["Enabled"]:
            continue
        bundle = _contained(root, "OC/Kexts/" + entry["BundlePath"])
        info_path = _contained(bundle, entry["PlistPath"])
        info = plistlib.loads(info_path.read_bytes())
        executable = entry.get("ExecutablePath", "")
        if info.get("CFBundleExecutable"):
            if executable != "Contents/MacOS/" + info["CFBundleExecutable"]:
                raise ValueError("Kext executable path does not match Info.plist")
            if not _contained(bundle, executable).is_file():
                raise ValueError("Enabled kext executable missing")
        identifier = info["CFBundleIdentifier"]
        if identifier in enabled:
            raise ValueError("Duplicate enabled kext ID: " + identifier)
        enabled[identifier] = {"index": index, "version": info["CFBundleVersion"]}
        if identifier == MELLOW_ID:
            mellow_entries.append(index)
    return root, config, enabled, mellow_entries


def _lilu_entry(root, config, *, enabled):
    candidates = []
    for entry in config["Kernel"]["Add"]:
        bundle = _contained(root, "OC/Kexts/" + entry["BundlePath"])
        info_path = _contained(bundle, entry["PlistPath"])
        if not info_path.is_file():
            continue
        info = plistlib.loads(info_path.read_bytes())
        if info.get("CFBundleIdentifier") == "as.vit9696.Lilu":
            candidates.append((entry, bundle, info))
    if len(candidates) != 1:
        raise ValueError("Supply exactly one Lilu entry and reference bundle in EFI")
    entry, bundle, info = candidates[0]
    if entry["Enabled"] is not enabled:
        raise ValueError("Lilu must be enabled for EFI deployment and disabled in Kernel/Add for root-patch deployment (disk-only dependency)")
    if entry.get("ExecutablePath") != "Contents/MacOS/" + info.get("CFBundleExecutable", "") or not _contained(bundle, entry["ExecutablePath"]).is_file():
        raise ValueError("Lilu reference executable missing or inconsistent")
    return entry, bundle, info


def plan(*, mode=None, deployment="root-patch", payload_dir=None, efi=None, settings=None):
    context, deployment, directory, efi = configuration(mode=mode, deployment=deployment,
        payload_dir=payload_dir, efi=efi, settings=settings)
    context.require_native_plan()
    if deployment == "disabled":
        raise ValueError("Choose EFI or root-patch deployment")
    from .payload import load_payload
    payload = load_payload(directory, mode=context.mode.value)
    if not efi:
        raise ValueError("Supply the target's OpenCore EFI to check Lilu and duplicate Mellow injection")
    root, config, enabled, duplicate = inspect_efi(efi)
    if duplicate:
        raise ValueError("Mellow is already enabled in this EFI; choose one deployment route")
    for kind in ("Force", "Block"):
        if any(e.get("Enabled") and e.get("Identifier") in (MELLOW_ID, "as.vit9696.Lilu")
               for e in config["Kernel"].get(kind, [])):
            raise ValueError("Resolve Mellow/Lilu Kernel/Force or Kernel/Block entries before choosing a deployment")
    lilu_entry, _, lilu_info = _lilu_entry(root, config, enabled=deployment == "efi")
    from packaging.version import Version
    if Version(lilu_info["CFBundleVersion"]) < Version("1.6.4"):
        raise ValueError("Mellow requires Lilu 1.6.4 or newer")
    if lilu_entry.get("Arch", "Any") not in ("Any", "x86_64"):
        raise ValueError("Lilu entry does not cover x86_64")
    minimum, maximum = lilu_entry.get("MinKernel", ""), lilu_entry.get("MaxKernel", "")
    if (minimum and Version(minimum) > Version("25.0.0")) or (maximum and Version(maximum) < Version("25.99.99")):
        raise ValueError("Lilu entry must cover the bundled payload's Darwin 25 range")
    return {"ok": True, "status": "prepared_plan", "execution": context.as_dict(),
        "deployment": deployment, "payload": str(payload.root),
        "source_commit": payload.source_commit, "required_boot_args": list(payload.required_boot_args),
        "patches": payload.patches() if deployment == "root-patch" else {},
        "efi_supplied_not_boot_attested": True, "requires_native_preflight": True,
        "lilu_route": "efi" if deployment == "efi" else "disk-only",
        "root_patch_executed": False, "native_metal_verified": False}


def validate_live(constants):
    """Before any mount/write, validate the actual x86 host and diagnostic prerequisites."""
    execution_for(constants).require_native_apply()
    payload = selected_payload(constants)
    if payload is None:
        return
    if constants.detected_os != 25:
        raise ValueError("The bundled Mellow diagnostic payload requires Darwin 25")
    if not any(g.vendor_id == 0x8086 and g.device_id == 0x7D41
               for g in (constants.computer.gpus or [])):
        raise ValueError("The bundled diagnostic kext targets physical Intel 8086:7D41")
    plan(mode=constants.execution_mode, deployment="root-patch",
         payload_dir=constants.mellow_payload_path, efi=constants.mellow_efi_path)
    from opencore_legacy_patcher.support import utilities
    if not utilities.check_kext_loaded("as.vit9696.Lilu"):
        raise ValueError("The running macOS kernel has not loaded Lilu")
    if utilities.check_kext_loaded(MELLOW_ID):
        raise ValueError("Mellow is already loaded; revert the prior deployment before installing another route")
    import subprocess
    result = subprocess.run(["/usr/sbin/sysctl", "-n", "kern.bootargs"],
        capture_output=True, text=True, timeout=5, check=True)
    if any(arg not in result.stdout.split() for arg in payload.required_boot_args):
        raise ValueError("Boot with -mellowdiag before applying this diagnostic payload")
    # EFI injection is runtime state, not a kmutil link input. Require an
    # existing on-disk dependency with the same bytes as the reviewed EFI.
    # This integration never silently installs a second Lilu deployment.
    validate_disk_lilu(constants.mellow_efi_path)
    validate_kdk(constants)


def validate_disk_lilu(efi, extensions="/Library/Extensions"):
    root, config, _, _ = inspect_efi(efi)
    entry, source, _ = _lilu_entry(root, config, enabled=False)
    directory = Path(extensions)
    matches = []
    for candidate in directory.glob("*.kext"):
        info = _contained(candidate, "Contents/Info.plist")
        if info.is_file() and plistlib.loads(info.read_bytes()).get("CFBundleIdentifier") == "as.vit9696.Lilu":
            matches.append(candidate)
    if len(matches) != 1:
        raise ValueError("Root-patch kmutil linking requires one existing on-disk Lilu in /Library/Extensions; EFI injection alone is insufficient")
    installed = matches[0]
    for relative in ("Contents/Info.plist", entry["ExecutablePath"]):
        if _contained(installed, relative).read_bytes() != _contained(source, relative).read_bytes():
            raise ValueError("On-disk and EFI Lilu differ; resolve the dependency deployment before root patching")
    def inventory(bundle):
        result = {}
        for path in bundle.rglob("*"):
            name = path.relative_to(bundle).as_posix()
            checked = _contained(bundle, name)
            if checked.is_file():
                result[name] = checked.read_bytes()
        return result
    if inventory(installed) != inventory(source):
        raise ValueError("On-disk and EFI Lilu bundle contents differ")


def validate_kdk(constants):
    from opencore_legacy_patcher.support.kdk_handler import KernelDebugKitObject
    kdk = KernelDebugKitObject(constants, constants.detected_os_build, constants.detected_os_version, passive=True)
    build = kdk.kdk_url_build
    if not build and kdk.kdk_installed_path:
        build = Path(kdk.kdk_installed_path).stem.rsplit("_", 1)[-1]
    if not kdk.success or build != constants.detected_os_build:
        raise ValueError("Mellow primary kernel collection requires an available exact-build KDK")


def require_journal_privileges(data_root="/"):
    journal = Path(data_root) / "Library/Application Support/26x86/Mellow/transaction/active"
    if journal.exists() and os.geteuid() != 0:
        raise PermissionError("Mellow restore requires the complete worker to run through sudo")
    return journal.exists()


def prepare_efi(efi, output, *, mode=None, payload_dir=None, settings=None, deployment="efi"):
    """Copy to a new EFI directory; no ESP mount, active config edit or kext load."""
    if deployment not in ("efi", "root-patch"):
        raise ValueError("Unknown EFI preparation route")
    # Begin with a reviewed EFI-injection dependency, then produce a separate
    # disk-only root-patch configuration. Never change the active source EFI.
    report = plan(mode=mode, deployment="efi", payload_dir=payload_dir, efi=efi, settings=settings)
    root, original, enabled, _ = inspect_efi(efi)
    output = Path(output).expanduser().resolve()
    if output.exists() or output == Path(output.anchor) or root in output.parents or output in root.parents:
        raise ValueError("Output must be a new directory outside the source EFI")
    from .payload import load_payload
    payload = load_payload(Path(report["payload"]), mode=report["execution"]["mode"])
    source = payload.root / "root/Library/Extensions/Mellow.kext"
    if not source.is_dir():
        raise ValueError("This payload has no Mellow.kext for EFI injection")
    # Reject symlinks throughout the source before recursive copy or replacement.
    if any(p.is_symlink() or getattr(p.lstat(), "st_file_attributes", 0) & 0x400 for p in root.rglob("*")):
        raise ValueError("Source EFI contains a symlink")
    shutil.copytree(root, output)
    target = output / "OC/Kexts/Mellow.kext"
    if target.exists() and deployment == "efi":
        if not target.resolve().is_relative_to(output):
            raise ValueError("Mellow target escapes new output")
        shutil.rmtree(target)
    if deployment == "efi":
        shutil.copytree(source, target)
        for source_file in source.rglob("*"):
            if source_file.is_file() and source_file.read_bytes() != (target / source_file.relative_to(source)).read_bytes():
                raise ValueError("Copied Mellow payload readback mismatch")
    config = copy.deepcopy(original)
    # An inactive older Mellow entry is replaced, never enabled in addition.
    config["Kernel"]["Add"] = [e for e in config["Kernel"]["Add"]
        if e["BundlePath"] != "Mellow.kext"]
    if deployment == "efi":
        config["Kernel"]["Add"].append({"Arch": "x86_64", "BundlePath": "Mellow.kext",
            "Comment": "Mellow diagnostic; Metal acceleration is not verified", "Enabled": True,
            "ExecutablePath": "Contents/MacOS/Mellow", "MaxKernel": "25.99.99", "MinKernel": "25.0.0",
            "PlistPath": "Contents/Info.plist"})
    else:
        entry, _, _ = _lilu_entry(output, config, enabled=True)
        entry["Enabled"] = False
    arguments = config["NVRAM"]["Add"][APPLE_GUID].get("boot-args", "").split()
    for argument in payload.required_boot_args:
        if argument not in arguments:
            arguments.append(argument)
    config["NVRAM"]["Add"][APPLE_GUID]["boot-args"] = " ".join(arguments)
    deletes = config["NVRAM"].setdefault("Delete", {}).setdefault(APPLE_GUID, [])
    if "boot-args" not in deletes:
        deletes.append("boot-args")
    (output / "OC/config.plist").write_bytes(plistlib.dumps(config, sort_keys=False))
    _, _, after, duplicates = inspect_efi(output)
    if deployment == "root-patch":
        report = plan(mode=mode, deployment=deployment, payload_dir=payload_dir, efi=output, settings=settings)
        if duplicates or "as.vit9696.Lilu" in after:
            raise ValueError("Root-patch EFI must not inject Mellow or Lilu")
    elif len(duplicates) != 1 or after[MELLOW_ID]["index"] <= after["as.vit9696.Lilu"]["index"]:
        raise ValueError("Prepared EFI dependency order failed")
    return {**report, "status": "efi_prepared_not_booted", "output": str(output), "source_efi_modified": False}
