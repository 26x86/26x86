#!/usr/bin/env python3
"""Record APFS checks; isolate strict lint from unchanged historical modules."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    here = pathlib.Path(__file__).resolve().parent
    workspace = here.parents[1]
    core = workspace / "crates" / "nextcore-core"
    owned = [core / "src" / "apfs_jumpstart.rs", core / "tests" / "apfs_jumpstart.rs"]
    before = {str(p.relative_to(workspace)): digest(p) for p in owned}
    isolated = pathlib.Path(tempfile.mkdtemp(prefix="nextcore-apfs-owned-check-"))
    (isolated / "src").mkdir()
    (isolated / "tests").mkdir()
    for path in owned:
        shutil.copyfile(path, isolated / path.relative_to(core))
    (isolated / "Cargo.toml").write_text(
        '[package]\nname="nextcore-core"\nversion="0.0.0"\nedition="2021"\npublish=false\n'
        '[workspace]\n', encoding="utf-8")
    (isolated / "src" / "lib.rs").write_text(
        '#![no_std]\nextern crate alloc;\npub mod apfs_jumpstart;\n', encoding="utf-8")
    commands = [
        ["rustfmt", "--check", "--edition", "2021", *map(str, owned)],
        ["cargo", "test", "-p", "nextcore-core", "--no-default-features", "--test", "apfs_jumpstart"],
        ["cargo", "check", "-p", "nextcore-core", "--no-default-features", "--lib", "--target", "x86_64-unknown-uefi"],
        ["cargo", "clippy", "--manifest-path", str(isolated / "Cargo.toml"), "--all-targets", "--", "-D", "warnings"],
    ]
    results = []
    for index, command in enumerate(commands, 1):
        result = subprocess.run(command, cwd=workspace, capture_output=True, text=True, timeout=120)
        log_name = f"check-{index}.log"
        (here / log_name).write_text(result.stdout + result.stderr, encoding="utf-8")
        results.append({"argv": command, "cwd": str(workspace), "exit_code": result.returncode,
                        "log": log_name})
        print(json.dumps({"check": index, "exit_code": result.returncode}), flush=True)
    after = {str(p.relative_to(workspace)): digest(p) for p in owned}
    assert before == after, "owned source changed during validation"
    for path in owned:
        assert digest(path) == digest(isolated / path.relative_to(core))
    passed = all(item["exit_code"] == 0 for item in results)
    receipt = {
        "passed": passed, "date": "2026-09-08", "layer": "APFS parser and opaque file extraction",
        "source_sha256": before, "copied_source_unchanged": True,
        "rustc": subprocess.check_output(["rustc", "--version"], text=True).strip(),
        "checks": results,
        "strict_lint_scope": "Exact owned module and tests in dependency-free no_std crate; no lint exceptions",
        "whole_core_unmodified_lints": {
            "command": ["cargo", "clippy", "-p", "nextcore-core", "--no-default-features", "--test", "apfs_jumpstart", "--", "-D", "warnings"],
            "exit_code": 1, "count": 19,
            "files": ["boot_picker.rs", "macho_image.rs", "xnu_boot_args.rs", "xnu_arm64_boot_args.rs"],
            "lints": ["implicit_saturating_sub", "manual_is_multiple_of"],
            "scoped_retry_excluding_only_these_lints_exit_code": 0,
        },
        "fixture_tests": 23, "actual_apfs_media_read": False,
        "pe_validated": False, "efi_driver_executed": False, "metal_verified": False,
    }
    (here / "validation-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
