#!/usr/bin/env python3
"""Execute the integrated memory service and bounded trace proofs in x86 OVMF."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()



def validate_bypass_rejection(output: Path, execution: dict) -> None:
    """Require an actual provider rejection receipt, not an arbitrary exit-one crash."""
    receipt = json.loads((output / "bypass-negative.json").read_text())
    cases = receipt.get("cases")
    if (receipt.get("schema") != "nextcore.efi-provider-observations.v1"
            or receipt.get("passed") is not False
            or not isinstance(cases, list) or len(cases) != 1):
        raise RuntimeError("Bypass control did not produce its expected failure receipt")
    case = cases[0]
    checks = case.get("checks", {})
    missing_provider = {"provider_build_marker", "provider_result_present", "provider_abi",
                        "provider_provider_status", "provider_fetch_requests", "provider_data_requests",
                        "provider_completed_data_operations", "provider_last_address", "provider_guest_far"}
    expected_checks = missing_provider | {"diagnostic_completed", "inputs_preserved",
                                          "one_native_entry_per_executed_instruction"}
    expected_failures = missing_provider | ({"one_native_entry_per_executed_instruction"}
                                           if execution["compiled_blocks"] != 18 else set())
    if (case.get("kind") != "scalar" or case.get("name") != "byte-signed"
            or case.get("passed") is not False or case.get("observed") != {}
            or case.get("execution") != execution or set(checks) != expected_checks
            or any(type(value) is not bool for value in checks.values())
            or {key for key, value in checks.items() if value is False} != expected_failures
            or case.get("serial_sha256") != digest(output / "bypass/serial.log")
            or case.get("report_sha256") != digest(output / "bypass/report.json")):
        raise RuntimeError("Bypass control failed for a different reason or unrelated execution")



def validate_tiered_provider(output: Path, fixtures: Path) -> None:
    """The combined variant must use the service for every bounded-loop fetch."""
    spec = importlib.util.spec_from_file_location("provider_observation", fixtures / "verify_provider_results.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Provider observation helper is unavailable")
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    case = output / "tiers/tiered256"
    observed, marker = observer.observation(case)
    execution = json.loads((case / "report.json").read_text())["execution"]
    expected = {"abi": 1, "provider_status": 0, "guest_far": 0, "fetch_requests": 256,
                "data_requests": 0, "completed_data_operations": 0}
    if (not marker or any(observed.get(key) != value for key, value in expected.items())
            or execution.get("status") != 5 or execution.get("retired") != 256
            or execution.get("compiled_blocks") != 256
            or execution.get("registers", {}).get("x0") != 128
            or execution.get("exception", {}).get("esr") != 0):
        raise RuntimeError("Bounded-tier execution did not use the checked memory service")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("provider-efi", "direct-efi", "tiered-efi", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    tools = Path(__file__).resolve().parent
    fixtures = tools.parent / "artifacts/arm-memory-provider-20260909"
    tiers = tools.parent / "artifacts/arm-tiered-trace-20260909"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    provider, direct, tiered = [p.resolve(strict=True) for p in
                                (args.provider_efi, args.direct_efi, args.tiered_efi)]
    inputs = [provider, direct, tiered, Path(__file__).resolve(),
              tools / "trace_arm_jit_ovmf.py", tools / "verify_arm_jit_ovmf.py",
              tools / "build_arm64_handoff_probe.py"]
    inputs += list(fixtures.glob("*.py")) + list(fixtures.glob("*.S"))
    inputs += [tiers / "verify_tiered_budget_ovmf.py", tiers / "tiered_budget_probe.S"]
    before = {str(p): digest(p) for p in inputs}
    records = []

    def run(name: str, command: list[str], expected: int = 0) -> None:
        with (output / (name + ".log")).open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"})
        records.append({"name": name, "command": command,
                        "exit_code": result.returncode, "expected_exit_code": expected})
        print(name, result.returncode, flush=True)
        if result.returncode != expected:
            raise RuntimeError(f"{name} failed; inspect its log")

    passed = False
    try:
        for kind in ("scalar", "pair"):
            run(kind, [sys.executable, str(fixtures / f"verify_{kind}_ovmf.py"),
                       "--efi", str(provider), "--tools", str(tools),
                       "--output", str(output / kind)])
        run("observations", [sys.executable, str(fixtures / "verify_provider_results.py"),
                             "--scalar", str(output / "scalar"), "--pair", str(output / "pair"),
                             "--output", str(output / "observations.json")])
        run("edges", [sys.executable, str(fixtures / "run_provider_edges.py"),
                      "--efi", str(provider), "--tools", str(tools), "--output", str(output / "edges")])
        commands = json.loads((output / "scalar/commands.json").read_text())
        command = next(c.copy() for c in commands if any("trace_arm_jit_ovmf.py" in arg for arg in c))
        command[command.index("--efi") + 1] = str(direct)
        command[command.index("--output") + 1] = str(output / "bypass")
        run("direct-bypass", command)
        execution = json.loads((output / "bypass/report.json").read_text())["execution"]
        regs = execution["registers"]
        if (execution["status"], execution["retired"], regs["x0"], regs["x1"], regs["x2"]) != (
                1, 18, 129, 0xffffffffffffff81, 0xffffff81):
            raise RuntimeError("Direct control did not execute the original authored byte case")
        run("bypass-rejected", [sys.executable, str(fixtures / "verify_provider_results.py"),
                                "--byte-case", str(output / "bypass"),
                                "--output", str(output / "bypass-negative.json")], expected=1)
        validate_bypass_rejection(output, execution)
        run("tiers", [sys.executable, str(tiers / "verify_tiered_budget_ovmf.py"),
                      "--tools", str(tools), "--efi", str(tiered), "--default-efi", str(provider),
                      "--output", str(output / "tiers")])
        validate_tiered_provider(output, fixtures)
        passed = True
    finally:
        after = {str(p): digest(p) for p in inputs}
        receipt = {"schema": "nextcore.integrated-efi-memory-proof.v1", "passed": passed and before == after,
                   "commands": records, "input_sha256_before": before, "input_sha256_after": after,
                   "provider_cases": 23 if passed else None, "tiered_cases": 8 if passed else None,
                   "actual_x86_firmware_cases": 26 if passed else None, "cli_rejections": 6 if passed else None,
                   "direct_bypass_negative_detected": passed, "transport_failure_variant_executed": False,
                   "native_mmu_verified": False, "macos_boot_verified": False, "guest_metal_verified": False}
        (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
