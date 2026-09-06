"""26x86 support artifact identity receipts; first-party BSD-4-Clause code.

Receipts bind an existing payload to declared deployment metadata. They do not
claim that the payload implements that architecture or that macOS boots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SCHEMA = "26x86.support-artifact/1"
ROLES = ("root-support-package", "gpu-compiler-abi")


def identity(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Identity input must be a regular file")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Input changed while hashing")
    if not after.st_size:
        raise ValueError("Empty identity input")
    return {"name": path.name, "size": after.st_size, "sha256": digest.hexdigest()}


def _target(major, build, architecture, abi):
    if type(major) is not int or major not in (26, 27):
        raise ValueError("Target must be macOS 26 or 27")
    if not isinstance(build, str) or not re.fullmatch(r"[0-9]{2}[A-Z][0-9]+[a-z]?", build):
        raise ValueError("Exact macOS build is required")
    if not build.startswith(str(major - 1)):
        raise ValueError("macOS major and Darwin build prefix disagree")
    if architecture not in ("x86_64", "arm64"):
        raise ValueError("Target host architecture must be x86_64 or arm64")
    if not isinstance(abi, str) or not abi.strip() or len(abi) > 256:
        raise ValueError("Explicit runtime/compiler ABI identifier is required")
    return {"macos_major": major, "os_build": build,
            "architecture": architecture, "runtime_abi": abi}


def create_receipt(artifact, *, source_repo, role, macos_major, os_build,
                   architecture, runtime_abi, license_file, compiler_file=None):
    if role not in ROLES:
        raise ValueError("Unknown artifact role")
    target = _target(macos_major, os_build, architecture, runtime_abi)
    if role == "gpu-compiler-abi" and compiler_file is None:
        raise ValueError("GPU compiler ABI receipts require the actual compiler binary")
    repo = Path(source_repo).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True, timeout=15).strip()
    revision = git("rev-parse", "HEAD")
    url = git("remote", "get-url", "origin")
    if not re.fullmatch(r"[0-9a-f]{40,64}", revision) or not re.fullmatch(r"https://[^@\s]+", url):
        raise ValueError("Source repository requires an immutable revision and public HTTPS origin")
    result = {"schema": SCHEMA, "role": role, "target": target,
        "artifact": identity(artifact), "license": identity(license_file),
        "source": {"url": url, "revision": revision, "working_tree_dirty": bool(git("status", "--porcelain"))},
        "architecture_observation": "declared-deployment-target",
        "compatibility_verified": False, "hardware_verified": False, "can_apply": False}
    if compiler_file is not None:
        result["compiler"] = identity(compiler_file)
    return result


def verify_receipt(receipt_path, artifact, *, macos_major, os_build,
                   architecture, runtime_abi, license_file, compiler_file=None):
    """Verify expected host/build/ABI and bytes; no payload execution or install."""
    report = {"ok": False, "can_apply": False, "errors": []}
    try:
        receipt = Path(receipt_path)
        if receipt.stat().st_size > 1024 * 1024:
            raise ValueError("Receipt exceeds size limit")
        data = json.loads(receipt.read_text(encoding="utf-8"))
        if data.get("schema") != SCHEMA or data.get("role") not in ROLES:
            raise ValueError("Unknown artifact receipt schema or role")
        if data.get("target") != _target(macos_major, os_build, architecture, runtime_abi):
            raise ValueError("Artifact receipt target/build/ABI mismatch")
        if data.get("artifact") != identity(artifact) or data.get("license") != identity(license_file):
            raise ValueError("Artifact or license identity mismatch")
        source = data.get("source", {})
        if not re.fullmatch(r"[0-9a-f]{40,64}", source.get("revision", "")) or not re.fullmatch(r"https://[^@\s]+", source.get("url", "")):
            raise ValueError("Missing source revision or provenance")
        if data["role"] == "gpu-compiler-abi" and compiler_file is None:
            raise ValueError("Compiler binary required to verify GPU ABI receipt")
        if "compiler" in data and (compiler_file is None or data["compiler"] != identity(compiler_file)):
            raise ValueError("Compiler identity mismatch")
        if data["role"] == "gpu-compiler-abi" and "compiler" not in data:
            raise ValueError("Compiler identity missing")
        report.update(ok=True, role=data["role"], target=data["target"],
                      compatibility_verified=False, hardware_verified=False)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        report["errors"].append(str(exc))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Record existing support artifact bytes and exact target; never patch or install")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-repo", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--role", choices=ROLES, required=True)
    parser.add_argument("--macos-major", type=int, choices=(26,27), required=True)
    parser.add_argument("--os-build", required=True)
    parser.add_argument("--architecture", choices=("x86_64","arm64"), required=True)
    parser.add_argument("--runtime-abi", required=True)
    parser.add_argument("--license-file", required=True)
    parser.add_argument("--compiler-file")
    args = parser.parse_args(argv)
    try:
        data = create_receipt(args.artifact, source_repo=args.source_repo, role=args.role,
            macos_major=args.macos_major, os_build=args.os_build, architecture=args.architecture,
            runtime_abi=args.runtime_abi, license_file=args.license_file, compiler_file=args.compiler_file)
        # Exclusive creation keeps an existing build receipt immutable.
        with Path(args.output).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
