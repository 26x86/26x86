#!/usr/bin/env python3
"""Run only authored bare-metal Arm code; preserve raw permission observations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(qemu, elf, out, seconds, cpu):
    endpoint = out / "qmp.sock"
    command = [qemu, "-machine", "virt,virtualization=off,secure=off", "-cpu", cpu,
               "-m", "128", "-display", "none", "-serial", "none", "-monitor", "none",
               "-nic", "none", "-qmp", f"unix:{endpoint},server=on,wait=off", "-kernel", str(elf)]
    start = time.monotonic()
    hard_deadline = start + seconds
    io_deadline = hard_deadline - 6
    deadline = io_deadline - 2
    completed = False
    with (out / "qemu.log").open("wb") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log, start_new_session=True)
        try:
            while not endpoint.exists():
                assert process.poll() is None and time.monotonic() < deadline, "QMP startup failed"
                time.sleep(.05)
            with socket.socket(socket.AF_UNIX) as sock:
                sock.settimeout(3)
                sock.connect(str(endpoint))
                stream = sock.makefile("rwb", buffering=0)
                json.loads(stream.readline())

                def qmp(execute, arguments=None):
                    request = {"execute": execute}
                    if arguments is not None:
                        request["arguments"] = arguments
                    stream.write((json.dumps(request) + "\n").encode())
                    while True:
                        remaining = io_deadline-time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("QMP total observation deadline reached")
                        sock.settimeout(min(3, remaining))
                        response = json.loads(stream.readline())
                        assert "error" not in response, response
                        if "return" in response:
                            return response["return"]

                qmp("qmp_capabilities")
                while time.monotonic() < deadline:
                    registers = qmp("human-monitor-command", {"command-line": "info registers"})
                    if "X00=00000000000006a1" in registers:
                        completed = True
                        break
                    time.sleep(.05)
                (out / "registers.txt").write_text(registers)
                qmp("stop")
                qmp("human-monitor-command", {"command-line": f'pmemsave 0x41000000 65536 "{out / "raw.bin"}"'})
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
            (out / "process.json").write_text(json.dumps({"command": command, "completed": completed,
                "reaped": process.poll() is not None, "returncode": process.returncode,
                "elapsed_seconds": time.monotonic()-start, "timeout_seconds": seconds}, indent=2)+"\n")
    assert completed, "Authored guest did not complete; raw RAM and registers preserved"
    assert time.monotonic() <= hard_deadline, "Total QEMU deadline exceeded"


def validate(raw, granule):
    words = struct.unpack("<" + "Q"*(len(raw)//8), raw)
    assert words[0] == 0x4849455241524348 and words[1] == granule and words[6] == 4
    tcr = ((17 | (17 << 16) | (1 << 30) | (2 << 14)) if granule == 16384
           else (16 | (16 << 16) | (2 << 30))) | (1 << 23) | (5 << 32)
    assert words[2] == tcr and words[3] == 0x30d00801
    assert words[16] == 0x44 and not(words[15] & (granule-1))
    assert words[24] == 0 and ((words[23] >> 8) & 255) == 0, "EL2/EL3 must be absent"
    assert words[22] == (1 if granule == 16384 else 0)
    assert (words[4] & 15) >= 5, "Hardware model lacks configured 48-bit PA"
    if granule == 16384:
        assert ((words[4] >> 20) & 15) in (1, 2), "16K granule not supported"
    else:
        assert ((words[4] >> 28) & 15) in (0, 1), "4K granule not supported"
    assert words[7] == (150 if granule == 16384 else 156), words[7]
    identities = [(kind, ap, parent, el, access) for kind in range(11) for ap in range(4)
                  for parent in range(4) if not kind or (ap == 1 and parent == 3)
                  if not(kind == 9 and granule == 16384)
                  for el in range(2) for access in range(3)]
    rows = []
    failures = []
    for n in range(words[7]):
        row_words = words[32+n*24:56+n*24]
        kind, ap, parent, el, access, success, esr, far, elr, value, memory, leaf, p1, p2, rtcr, rsctlr = row_words[:16]
        p0 = row_words[16]
        assert (kind, ap, parent, el, access) == identities[n]
        case_tcr = (tcr & ~(7 << 32)) | (2 << 32) if kind == 8 else tcr
        ec, fsc = esr >> 26, esr & 63
        el0_data = bool(ap & 1) and not(parent & 1)
        writable = not(ap & 2) and not(parent & 2)
        if access == 0:
            allowed = bool(el) or el0_data
        elif access == 1:
            allowed = writable and (bool(el) or el0_data)
        else:
            allowed = not(el and el0_data and writable)
            allowed &= not(el and kind in (1, 3)) and not(not el and kind in (2, 4))
        expected_fsc = 7 if kind == 6 else 11 if kind == 7 else 3 if kind == 8 else 15
        if kind in (6, 7, 8):
            allowed = False
        row = dict(granule=granule, kind=kind, leaf_ap=ap, parent_ap=parent, el=el,
                   access=["read", "write", "fetch"][access], success=bool(success),
                   expected_success=allowed, esr=hex(esr), ec=ec, fsc=fsc, far=hex(far),
                   exception_pc=hex(elr), expected_resume_pc=hex(words[14]), value=hex(value),
                   memory_after=hex(memory), leaf_descriptor=hex(leaf),
                   ancestor_descriptors=[hex(p0), hex(p1), hex(p2)], tcr=hex(rtcr), sctlr=hex(rsctlr),
                   descriptor_pa=hex(words[21]), output_pa=hex(words[17]),
                   ttbr0=hex(row_words[21]), mair=hex(row_words[22]),
                   configured_pa_bits=40 if kind == 8 else 48)
        errors = []
        if (p0, p1, p2, leaf) != tuple(row_words[17:21]):
            errors.append("descriptor modified by access")
        if (row_words[21], row_words[22], row_words[23]) != (words[15], 0x44, 0xd65f03c0):
            errors.append("translation controls or instruction modified")
        if success != allowed:
            errors.append("permission outcome")
        if (rtcr, rsctlr) != (case_tcr, 0x30d00801):
            errors.append("controls changed")
        if allowed:
            if ec != (0 if el else 0x15):
                errors.append("success exception class")
            if access == 0 and value != 0x1234:
                errors.append("load value")
        else:
            expected_ec = (0x21 if el else 0x20) if access == 2 else (0x25 if el else 0x24)
            expected_pc = 0x400000000000 if access == 2 else words[(8 if el else 11)+access]
            if (ec, fsc) != (expected_ec, expected_fsc):
                errors.append("fault EC/FSC")
            if far != 0x400000000000 + (0 if access == 2 else 128) or elr != expected_pc:
                errors.append("fault VA/PC")
            if access != 2 and ((esr >> 6) & 1) != (access == 1):
                errors.append("fault WnR")
        if memory != (0x6789 if allowed and access == 1 else 0x1234):
            errors.append("store effect")
        row["validation_errors"] = errors
        if errors:
            failures.append(row)
        rows.append(row)
    return dict(granule=granule, hardware_mmfr0=hex(words[4]), hardware_mmfr1=hex(words[5]),
                hardware_pfr0=hex(words[23]), initial_current_el=1, start_level=words[22],
                actual_ttbr0=hex(words[15]), actual_ttbr1=hex(words[24]), actual_mair=hex(words[16]),
                hcr_readback=None, scr_readback=None,
                hcr_scr_scope="Not read: EL2 and EL3 absent by machine configuration and actual PFR0; do not equate absence with a zero register readback",
                actual_tcr=hex(words[2]), actual_sctlr=hex(words[3]), rows=rows, failures=failures)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    assert 10 <= args.timeout <= 120
    source = Path(__file__).resolve().parent
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    files = [source/name for name in ("start.S", "oracle.c", "link.ld", "run.py", "CONTRACT.md")]
    before = {p.name: digest(p) for p in files}
    (out/"source").mkdir()
    for path in files:
        shutil.copyfile(path, out/"source"/path.name)
    qemu = shutil.which(args.qemu)
    assert qemu
    results = []
    for granule in (4096, 16384):
        directory = out / str(granule)
        directory.mkdir()
        elf = directory / "oracle.elf"
        command = ["clang", "--target=aarch64-none-elf", "-march=armv8-a", "-mgeneral-regs-only",
                   "-O2", "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-nostdlib",
                   f"-DGRANULE={granule}", "-Wl,-T,"+str(source/"link.ld"),
                   str(source/"start.S"), str(source/"oracle.c"), "-o", str(elf)]
        build = subprocess.run(command, capture_output=True, timeout=60)
        (directory / "build.log").write_bytes(build.stdout+build.stderr)
        assert build.returncode == 0, build.stderr.decode()
        cpu = "max"
        capture(qemu, elf, directory, args.timeout, cpu)
        result = validate((directory/"raw.bin").read_bytes(), granule)
        result["cpu"] = cpu
        result["elf_sha256"] = digest(elf)
        result["raw_sha256"] = digest(directory/"raw.bin")
        result["build_command"] = command
        result["process"] = json.loads((directory/"process.json").read_text())
        (directory/"observations.json").write_text(json.dumps(result, indent=2)+"\n")
        results.append(result)
    unchanged = before == {p.name: digest(p) for p in files}
    receipt = dict(passed=unchanged and not any(r["failures"] for r in results),
                   cases=sum(len(r["rows"]) for r in results), source_sha256=before,
                   sources_preserved=unchanged, qemu_sha256=digest(qemu),
                   qemu_version=subprocess.check_output([qemu,"--version"],text=True).splitlines()[0],
                   compiler_version=subprocess.check_output(["clang","--version"],text=True).splitlines()[0],
                   cpus=[r["cpu"] for r in results], original_images_used=False, physical_boot_verified=False,
                   scope="Actual authored Arm stage-1 page hierarchy; 48-bit IPS except twelve explicitly marked 40-bit address-size priority cases; TTBR0 only, cold per-case contexts; hardware feature IDs recorded, not equated with software",
                   results=results)
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"passed":receipt["passed"],"cases":receipt["cases"],"receipt":str(out/"receipt.json")}))
    raise SystemExit(0 if receipt["passed"] else 1)


if __name__ == "__main__":
    main()
