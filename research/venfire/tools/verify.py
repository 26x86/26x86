#!/usr/bin/env python3
"""Run unit and real synthetic guest checks and save one reproducible evidence set."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from venfire.backend import probe_backend
from venfire.artifacts import hash_artifact
from venfire.conformance import run_conformance
from venfire.host import detect_host
from build_backend import patch_series


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qemu", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    folder = args.output.absolute()
    folder.mkdir(parents=True, exist_ok=False)
    unit_code = None
    backend = {}
    before = after = None
    results = {}
    errors = []
    try:
        unit = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                              cwd=PROJECT, capture_output=True, text=True, timeout=120)
        unit_code = unit.returncode
        (folder / "unit-tests.txt").write_text(unit.stdout + unit.stderr, encoding="utf-8")
        backend = probe_backend(args.qemu)
        before = hash_artifact(backend["executable"]).sha256
        if unit_code == 0 and backend["tcg"] and backend["research_headless"]:
            for target in ("virt", "vmapple"):
                results[target] = run_conformance(backend["executable"], folder / target, target=target)
        else:
            errors.append("Unit tests or required backend capabilities failed")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if before is not None:
            try:
                after = hash_artifact(backend["executable"]).sha256
                if before != after:
                    errors.append("Backend binary changed during verification")
            except (OSError, ValueError) as exc:
                errors.append(f"Backend postcheck failed: {exc}")
    passed = not errors and unit_code == 0 and len(results) == 2 and all(r.get("passed") for r in results.values())
    report = {"schema": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
              "passed": passed, "host": {"os": platform.system(), "architecture": platform.machine()},
              "runtime_host_eligibility": detect_host().to_dict(),
              "unit_tests_exit_code": unit_code, "backend": backend, "errors": errors,
              "binary_sha256_before": before, "binary_sha256_after": after,
              "patches": [{"name": patch.name, "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()}
                          for patch in patch_series()],
              "guest_results": results, "macos_boot_verified": False,
              "real_mac_verified": False,
              "meaning": "Only self-authored ARM64 execution and control-plane tests are covered."}
    (folder / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
