#!/usr/bin/env python3
"""Authored actual-x86-EFI gate for the separately selected BP35 deep tier."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(name, value):
    return (name.encode().ljust(32, b"\0") + struct.pack("<I", len(value))
            + value.ljust((len(value) + 3) & ~3, b"\0"))


def run(command, log):
    process = subprocess.run(list(map(str, command)), capture_output=True, text=True,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    log.write_text(process.stdout + process.stderr)
    return process.returncode


def authored_checks(receipt, code, budget, mode, physical, entry_offset):
    execution = receipt.get("execution") or {}
    memory = execution.get("memory") or {}
    registers = execution.get("registers") or {}
    exception = execution.get("exception") or {}
    preserved = (receipt.get("original_inputs_preserved") and receipt.get("esp_copies_preserved")
                 and receipt.get("tool_sources_preserved"))
    markers = receipt.get("markers", [])
    if mode == "reject":
        return dict(returned=code == 1,
                    config_rejected=any("TRACE_CONFIG_INVALID" in marker for marker in markers),
                    no_entry=not any("TRACE_ENTER " in marker for marker in markers),
                    no_execution=receipt["execution"] is None, preserved=preserved)
    entries = [marker for marker in markers if marker.startswith("NXARMJIT: TRACE_ENTER ")]
    match = re.fullmatch(
        r"NXARMJIT: TRACE_ENTER entry=(0x[0-9a-f]+) x0=0 x1=(0x[0-9a-f]+) x2=0 x3=0 budget=(\d+)",
        entries[0]) if len(entries) == 1 else None
    entered_x1 = int(match.group(2), 16) if match else None
    retired = 4096 if mode == "clamped" else budget
    checks = dict(
        returned=code == 0, completed=receipt["diagnostic_completed"], budget=execution.get("status") == 5,
        exact_retirement=execution.get("retired") == retired, exact_fetches=memory.get("fetch_requests") == retired,
        exact_native=execution.get("compiled_blocks") == retired,
        provider=memory.get("abi") == 1 and memory.get("provider_status") == 0,
        no_data=memory.get("data_requests") == 0 and memory.get("completed_data_operations") == 0,
        pc=execution.get("pc") == physical + entry_offset + 8,
        last_fetch=memory.get("last_address") == physical + entry_offset + 4,
        entry=bool(match and int(match.group(1), 16) == physical + entry_offset
                   and int(match.group(3)) == budget and entered_x1 != 0),
        x1_preserved=entered_x1 is not None and registers.get("x1") == entered_x1,
        readback=registers.get("x0") == retired // 2 and registers.get("x2") == 0 and registers.get("x3") == 0x35,
        no_fault=execution.get("fault_instruction") == 0 and memory.get("guest_far") == 0
                 and exception.get("esr") == 0 and exception.get("vector") == 0,
        deep_build=receipt["deep_diagnostic_build_observed"],
        selection=receipt["deep_diagnostic_selected_observed"] == (mode in ("deep", "clamped")),
        preserved=preserved, os_not_claimed=receipt["macos_boot_verified"] is False and receipt["metal_verified"] is False)
    if mode == "clamped":
        checks["actual_deep_expectation_rejected"] = (execution.get("retired") != 16384
            and memory.get("fetch_requests") != 16384 and registers.get("x0") != 8192)
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("tools", "efi", "default-efi", "clamped-efi", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--cli-only", action="store_true")
    modes.add_argument("--recheck-provenance", action="store_true",
                       help="rerun all CLI rejections and one actual deep case using unchanged binaries")
    parser.add_argument("--core-source", type=Path)
    parser.add_argument("--efi-source", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    tools = args.tools.resolve(strict=True)
    if not args.cli_only and (args.core_source is None or args.efi_source is None):
        parser.error("actual proof requires --core-source and --efi-source provenance")
    sources = [Path(__file__).resolve(), source / "trace_deep_arm_jit_ovmf.py", source / "deep_budget_probe.S",
               tools / "build_arm64_handoff_probe.py", tools / "verify_arm_jit_ovmf.py"]
    if not args.cli_only:
        for root in (args.core_source.resolve(strict=True), args.efi_source.resolve(strict=True)):
            sources.extend(path for path in root.rglob("*") if path.is_file()
                           and path.suffix in (".rs", ".toml", ".md")
                           and "target" not in path.parts and ".git" not in path.parts)
    sources.extend(path.resolve(strict=True) for path in (args.efi, args.default_efi, args.clamped_efi))
    # This checkpoint precedes helper import, output creation, and every authored
    # assembly/image/DT construction step, as well as all subsequent execution.
    before = {str(path.resolve()): digest(path) for path in sources}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(tools))
    from build_arm64_handoff_probe import image, PHYSICAL, ENTRY_OFFSET
    obj, raw, kernel, dt = [output / name for name in ("loop.o", "loop.bin", "loop.kc", "diagnostic.dt")]
    subprocess.run(["clang", "--target=aarch64-none-elf", "-c", str(source / "deep_budget_probe.S"), "-o", str(obj)], check=True)
    subprocess.run(["llvm-objcopy", "-O", "binary", "--only-section=.text", str(obj), str(raw)], check=True)
    kernel.write_bytes(image(raw.read_bytes()))
    dt.write_bytes(struct.pack("<II", 1, 1) + prop("name", b"\0") + struct.pack("<II", 3, 0)
                   + prop("name", b"chosen\0") + prop("dram-base", struct.pack("<Q", 0x40000000))
                   + prop("dram-size", struct.pack("<Q", 67108864)))
    base = [sys.executable, source / "trace_deep_arm_jit_ovmf.py", "--tools", tools, "--kernel", kernel, "--device-tree", dt,
            "--physical-base", "0x40000000", "--virtual-base", "0xfffffe0000000000", "--memory-size", "67108864",
            "--kernel-physical", "0x42000000", "--host-memory-mib", "256", "--timeout", "60"]
    selected = ["--allow-incomplete-sptm-prefix", "--platform-profile", "nextcore-irq-compat-v1",
                "--instruction-budget", "16384", "--deep-diagnostic"]
    cli = [("missing-deep", selected[:-1]), ("conflicting-flags", selected + ["--tiered-diagnostic"]),
           ("absent-profile", [value for index, value in enumerate(selected) if index not in (1, 2)]),
           ("missing-handoff-authorization", selected[1:])]
    for budget in ("8192", "16383", "16385", "4096"):
        selection = selected.copy()
        selection[4] = budget
        cli.append(("wrong-budget-" + budget, selection))
    invalid_options = [
        ("irq-not-boolean", "--irq-level", "2"), ("fiq-not-boolean", "--fiq-level", "2"),
        ("irq-negative", "--irq-level", "-1"), ("pstate-invalid-mode", "--initial-pstate", "0"),
        ("pstate-unsupported-bits", "--initial-pstate", "0xbc5"),
        ("override-unsupported-bit", "--initial-override", "1"),
        ("override-invalid-irq-field", "--initial-override", "0x100000"),
        ("override-invalid-fiq-field", "--initial-override", "0xc00000"),
        ("vector-outside", "--vector-base", "0x60000000"),
        ("vector-unaligned", "--vector-base", "0x40000001"),
        ("vector-below", "--vector-base", "0x3ffff800"),
        ("vector-at-end", "--vector-base", "0x44000000"),
        ("vector-span-wrap", "--vector-base", "0xfffffffffffff800"),
        ("physical-span-wrap", "--physical-base", "0xffffffffff000000"),
        ("physical-exclusive-end-wrap", "--physical-base", "0xfffffffffc000000"),
        ("virtual-span-wrap", "--virtual-base", "0xffffffffff000000"),
        ("virtual-exclusive-end-wrap", "--virtual-base", "0xfffffffffc000000"),
        ("kernel-below", "--kernel-physical", "0x3fffc000"),
        ("kernel-at-end", "--kernel-physical", "0x44000000"),
        ("kernel-above", "--kernel-physical", "0x44004000")]
    cli.extend((name, selected + [option, value]) for name, option, value in invalid_options)
    cases = []
    for name, selection in cli:
        destination = output / name
        code = run([*base, "--efi", args.efi, "--output", destination, *selection], output / (name + ".log"))
        cases.append(dict(name=name, passed=code == 2 and not destination.exists(), returncode=code, kind="preflight-rejection"))
    if not args.cli_only:
        actual_cases = [("deep16384", args.efi, 16384, "deep")]
        if not args.recheck_provenance:
            actual_cases += [("old4096", args.efi, 4096, "tiered"), ("old64", args.efi, 64, "default"),
                             ("ordinary-firmware-rejects-deep", args.default_efi, 16384, "reject"),
                             ("clamped4096-semantic-negative", args.clamped_efi, 16384, "clamped")]
        for name, binary, budget, mode in actual_cases:
            destination = output / name
            selection = ["--allow-incomplete-sptm-prefix", "--platform-profile", "nextcore-irq-compat-v1", "--instruction-budget", str(budget)]
            if mode in ("deep", "reject", "clamped"):
                selection += ["--deep-diagnostic"]
            elif mode == "tiered":
                selection += ["--tiered-diagnostic"]
            code = run([*base, "--efi", binary, "--output", destination, *selection], output / (name + ".log"))
            path = destination / "report.json"
            if not path.is_file():
                cases.append(dict(name=name, passed=False, error="No actual EFI receipt", returncode=code))
                continue
            receipt = json.loads(path.read_text())
            checks = authored_checks(receipt, code, budget, mode, PHYSICAL, ENTRY_OFFSET)
            execution = receipt.get("execution") or {}
            cases.append(dict(name=name, passed=all(checks.values()), checks=checks, returncode=code,
                              retired=execution.get("retired"), fetches=(execution.get("memory") or {}).get("fetch_requests")))
            if mode == "deep" and all(checks.values()):
                mutated = copy.deepcopy(receipt)
                mutated["execution"]["registers"]["x1"] = 0
                mutation_checks = authored_checks(mutated, code, budget, mode, PHYSICAL, ENTRY_OFFSET)
                cases.append(dict(name="x1-corruption-reader-negative", kind="receipt-only-negative",
                                  passed=not mutation_checks["x1_preserved"] and not all(mutation_checks.values()),
                                  rejected_checks=[key for key, value in mutation_checks.items() if not value],
                                  actual_receipt_preserved=True))
    after = {str(path.resolve()): digest(path) for path in sources}
    report = dict(schema="nextcore.deep-arm-trace-authored-gate.v1", passed=all(case["passed"] for case in cases) and before == after,
                  source_preserved=before == after, cli_only=args.cli_only, recheck_provenance=args.recheck_provenance,
                  source_checkpoint="before helper import and all fixture compilation/construction", cases=cases,
                  source_sha256=before, source_sha256_after=after, macos_boot_verified=False, metal_verified=False)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(passed=report["passed"], report=str(output / "report.json"))))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
