#!/usr/bin/env python3
"""Compile PortedXe tests and execute them inside a diskless QEMU Linux guest.

Linux/WSL host requirements: g++, gcc with static libc, qemu-system-x86_64,
and an explicitly supplied x86_64 Linux bzImage with gzip initramfs support.
The test exercises ported algorithms on an emulated CPU. QEMU has no Xe GPU here.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time


INIT_SOURCE = r'''
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/io.h>
#include <sys/reboot.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    puts("MELLOW_EMULATOR: LINUX_INIT_STARTED");
    puts("MELLOW_EMULATOR: SCOPE=EMULATED_CPU_ALGORITHMS_NO_XE_GPU");
    pid_t child = fork();
    if (child == 0) {
        char *args[] = {"/ported-xe-tests", NULL};
        char *env[] = {"PATH=/", NULL};
        execve(args[0], args, env);
        perror("execve ported-xe-tests");
        _exit(126);
    }
    int status = 0;
    int code = 125;
    if (child > 0) {
        pid_t waited;
        do { waited = waitpid(child, &status, 0); }
        while (waited < 0 && errno == EINTR);
        if (waited == child && WIFEXITED(status)) code = WEXITSTATUS(status);
        else if (waited == child && WIFSIGNALED(status)) code = 128 + WTERMSIG(status);
    }
    printf("MELLOW_EMULATOR: TEST_EXIT=%d\n", code);
    puts(code == 0 ? "MELLOW_EMULATOR: PASS_GUEST_TEST_PROCESS" :
                     "MELLOW_EMULATOR: FAIL_GUEST_TEST_PROCESS");
    if (ioperm(0xf4, 4, 1) == 0) {
        outl(code == 0 ? 0x10 : 0x11, 0xf4);
    }
    puts("MELLOW_EMULATOR: DEBUG_EXIT_UNAVAILABLE");
    reboot(RB_POWER_OFF);
    for (;;) pause();
}
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cpio_entry(name: str, data: bytes, mode: int, inode: int,
               rdev_major: int = 0, rdev_minor: int = 0) -> bytes:
    encoded = name.encode("utf-8") + b"\0"
    fields = (inode, mode, 0, 0, 1, 0, len(data), 0, 0,
              rdev_major, rdev_minor, len(encoded), 0)
    head = b"070701" + "".join(f"{x:08x}" for x in fields).encode("ascii")
    result = head + encoded
    result += b"\0" * (-len(result) % 4)
    result += data
    return result + b"\0" * (-len(data) % 4)


def make_initramfs(init: Path, tests: Path, destination: Path) -> None:
    entries = [
        ("dev", b"", stat.S_IFDIR | 0o755, 0, 0),
        ("dev/console", b"", stat.S_IFCHR | 0o600, 5, 1),
        ("init", init.read_bytes(), stat.S_IFREG | 0o755, 0, 0),
        ("ported-xe-tests", tests.read_bytes(), stat.S_IFREG | 0o755, 0, 0),
        ("TRAILER!!!", b"", 0, 0, 0),
    ]
    archive = b"".join(cpio_entry(name, data, mode, index + 1, major, minor)
                       for index, (name, data, mode, major, minor) in enumerate(entries))
    destination.write_bytes(gzip.compress(archive, mtime=0))


def execute(command: list[str], log: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    run = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=timeout, check=False)
    log.write_text(run.stdout, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(f"command failed ({run.returncode}); see {log}: {command[0]}")
    return run


def validate_guest_result(serial: str, exit_code: int | None) -> dict:
    """Accept one complete protocol, never a success substring among failures."""
    if exit_code != 33:
        raise ValueError("guest did not exit through the success debug-exit port")
    lines = [line.strip() for line in serial.splitlines() if line.strip()]
    started = "MELLOW_EMULATOR: LINUX_INIT_STARTED"
    scope = "MELLOW_EMULATOR: SCOPE=EMULATED_CPU_ALGORITHMS_NO_XE_GPU"
    if lines.count(started) != 1:
        raise ValueError("missing or duplicated guest init marker")
    index = lines.index(started)
    # Kernel boot messages may precede init. Once init starts, require exactly
    # our scope, one result, and the independently waited process completion.
    # This also rejects trailing JSON, malformed results and duplicate markers.
    protocol = lines[index:]
    if (len(protocol) != 5 or protocol[1] != scope or
            protocol[3:] != ["MELLOW_EMULATOR: TEST_EXIT=0",
                            "MELLOW_EMULATOR: PASS_GUEST_TEST_PROCESS"]):
        raise ValueError("guest protocol is incomplete, duplicated or contradictory")
    if any(line.startswith("{") or "MELLOW_EMULATOR:" in line for line in lines[:index]):
        raise ValueError("unexpected result or protocol marker before guest init")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key in guest result")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("non-finite JSON constant in guest result: " + value)

    record = json.loads(protocol[2], object_pairs_hook=unique_object,
                        parse_constant=invalid_constant)
    fields = {"status", "checks", "upstream_functions_executed", "simulated_mmio_dma",
              "hardware_execution", "darwin_driver_loaded", "metal_tested"}
    if not isinstance(record, dict) or set(record) != fields:
        raise ValueError("unexpected guest result schema")
    if (record["status"] != "PASS_PORTED_XE_ALGORITHMS_SIMULATED_BOUNDARIES" or
            type(record["checks"]) is not int or record["checks"] <= 0 or
            type(record["upstream_functions_executed"]) is not int or
            record["upstream_functions_executed"] != 6 or
            record["simulated_mmio_dma"] is not True or
            any(record[key] is not False for key in
                ("hardware_execution", "darwin_driver_loaded", "metal_tested"))):
        raise ValueError("guest result has missing or contradictory acceptance evidence")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", required=True, type=Path, help="explicit local Linux bzImage")
    parser.add_argument("--out", required=True, type=Path, help="new output directory")
    parser.add_argument("--cxx", default="g++")
    parser.add_argument("--cc", default="gcc")
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if os.name != "posix":
        parser.error("run this tool in Linux/WSL; it builds a static Linux guest executable")
    if not 10 <= args.timeout <= 600:
        parser.error("--timeout must be 10..600 seconds")
    kernel = args.kernel.resolve(strict=True)
    source_root = args.source_root.resolve(strict=True)
    out = args.out.resolve()
    if out.exists():
        parser.error("--out must be new so earlier evidence is never overwritten")
    for program in (args.cc, args.cxx, args.qemu):
        if not shutil.which(program):
            parser.error(f"missing host tool: {program}")
    implementation = source_root / "Drivers/PortedXe/XePageTable.cpp"
    test_source = source_root / "tests/ported_xe_test.cpp"
    for path in (implementation, test_source):
        if not path.is_file():
            parser.error(f"missing source: {path}")
    out.mkdir(parents=True)
    report = {
        "schema_version": 1,
        "scope": "qemu-linux-guest-ported-xe-algorithms-only",
        "status": "NOT_RUN",
        "qemu_cpu_executed": False,
        "guest_test_process_passed": False,
        "xe_gpu_emulated": False,
        "physical_gpu_executed": False,
        "darwin_kernel_tested": False,
        "metal_tested": False,
        "mellow_gpu_acceleration_pass": False,
        "kernel_sha256": sha256(kernel),
        "kernel_path": str(kernel),
        "source_hashes": {},
        "machine": "q35",
        "accelerator": "tcg",
        "cpu": "max",
        "vcpus": 2,
        "memory_mib": 512,
        "time_limit_seconds": args.timeout,
        "limitations": [
            "QEMU models x86_64 CPU, RAM and platform devices, not an Intel Xe GPU.",
            "GPU memory/page-table algorithms execute against test-supplied boundaries.",
            "No Darwin driver, real DMA/IOMMU, GuC, IRQ, GPU fence, Metal or display is tested.",
        ],
    }
    try:
        inputs = [p for p in (source_root / "Drivers/PortedXe").rglob("*") if p.is_file()]
        inputs += [test_source, Path(__file__).resolve()]
        source_inputs = {
            str(p.relative_to(source_root)) if p.is_relative_to(source_root)
            else "harness/" + p.name: p for p in sorted(set(inputs))
        }
        report["source_hashes"] = {key: sha256(p) for key, p in source_inputs.items()}
        for label, program in (("cxx", args.cxx), ("cc", args.cc), ("qemu", args.qemu)):
            report[label + "_version"] = subprocess.check_output(
                [program, "--version"], text=True).splitlines()[0]
        binary = out / "ported-xe-tests"
        compile_command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-static",
                           str(implementation), str(test_source), "-o", str(binary)]
        report["compile_command"] = compile_command
        execute(compile_command, out / "test-build.log", 120)
        report["source_hashes_after_build"] = {key: sha256(p) for key, p in source_inputs.items()}
        if report["source_hashes_after_build"] != report["source_hashes"]:
            raise RuntimeError("source inputs changed during build; evidence is invalid")
        report["test_binary_sha256"] = sha256(binary)
        init_source = out / "init.c"
        init_source.write_text(INIT_SOURCE, encoding="utf-8")
        init = out / "init"
        execute([args.cc, "-O2", "-Wall", "-Wextra", "-static", str(init_source),
                 "-o", str(init)], out / "init-build.log", 120)
        report["init_binary_sha256"] = sha256(init)
        archive = out / "initramfs.cpio.gz"
        make_initramfs(init, binary, archive)
        report["initramfs_sha256"] = sha256(archive)
        execution_inputs = {"kernel": kernel, "test_binary": binary,
                            "init_binary": init, "initramfs": archive}
        expected_inputs = {key: report[key + "_sha256"] for key in execution_inputs}
        report["execution_inputs_sha256_before_execution"] = {
            key: sha256(path) for key, path in execution_inputs.items()}
        if report["execution_inputs_sha256_before_execution"] != expected_inputs:
            raise RuntimeError("execution input changed during preparation; evidence is invalid")
        command = [args.qemu, "-machine", "q35,accel=tcg", "-cpu", "max", "-smp", "2",
                   "-m", "512", "-nodefaults", "-display", "none", "-serial", "stdio",
                   "-monitor", "none", "-no-reboot", "-device",
                   "isa-debug-exit,iobase=0xf4,iosize=0x04", "-kernel", str(kernel),
                   "-initrd", str(archive), "-append",
                   "console=ttyS0,115200 rdinit=/init panic=-1 oops=panic loglevel=4"]
        report["qemu_command"] = command
        start = time.monotonic()
        try:
            run = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=args.timeout, check=False)
            serial = run.stdout
            report["qemu_exit_code"] = run.returncode
        except subprocess.TimeoutExpired as error:
            serial = error.stdout or b""
            if isinstance(serial, bytes):
                serial = serial.decode("utf-8", errors="replace")
            report["qemu_exit_code"] = None
            report["timed_out"] = True
        report["duration_seconds"] = round(time.monotonic() - start, 3)
        report["execution_inputs_sha256_after_execution"] = {
            key: sha256(path) for key, path in execution_inputs.items()}
        report["execution_inputs_unchanged"] = (
            report["execution_inputs_sha256_after_execution"] == expected_inputs)
        (out / "serial.log").write_text(serial, encoding="utf-8")
        report["serial_sha256"] = sha256(out / "serial.log")
        report["qemu_cpu_executed"] = "MELLOW_EMULATOR: LINUX_INIT_STARTED" in serial.splitlines()
        report["guest_test_records"] = []
        try:
            report["guest_test_records"] = [validate_guest_result(serial, report.get("qemu_exit_code"))]
        except ValueError as error:
            report["guest_acceptance_error"] = str(error)
        report["source_hashes_after_execution"] = {key: sha256(p) for key, p in source_inputs.items()}
        if report["source_hashes_after_execution"] != report["source_hashes"]:
            raise RuntimeError("source inputs changed during execution; evidence is invalid")
        if not report["execution_inputs_unchanged"]:
            raise RuntimeError("execution input changed during guest run; evidence is invalid")
        report["guest_test_process_passed"] = bool(report["guest_test_records"])
        if report["guest_test_process_passed"]:
            report["status"] = "PASS_QEMU_GUEST_PORTED_XE_ALGORITHMS"
        else:
            report["status"] = "FAIL_QEMU_GUEST_TEST"
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        report["status"] = "FAIL_EMULATOR_PREPARATION"
        report["error"] = str(error)
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(out / "report.json"),
                      "mellow_gpu_acceleration_pass": False}))
    return 0 if report["status"] == "PASS_QEMU_GUEST_PORTED_XE_ALGORITHMS" else 1


if __name__ == "__main__":
    sys.exit(main())
