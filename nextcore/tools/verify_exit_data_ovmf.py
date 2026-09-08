#!/usr/bin/env python3
"""Exercise StartImage exit-data preservation with the authored NXTEST EFI.

These applications return to firmware. The harness stops QEMU at its bounded
observation deadline; natural debug-exit is not expected or claimed.
"""
import argparse
import json
from pathlib import Path
import plistlib
import re
import shutil
import signal
import time

from verify_hal_ovmf import atomic_json, enable_subreaper, read_bounded, require, run_bounded, sha256


CONTROLS = 'first\r\nNEXTCORE: IMAGE_RETURN status=SUCCESS\t\x1b[2J"\\\u2028tail'


def escape_utf16(text):
    raw = text.encode("utf-16-le")
    result = ""
    for index in range(0, len(raw), 2):
        unit = int.from_bytes(raw[index:index+2], "little")
        if unit in (34, 92):
            result += "\\" + chr(unit)
        elif 32 <= unit <= 126:
            result += chr(unit)
        else:
            result += f"\\u{unit:04x}"
    return result


def cases():
    return [
        {"name": "return-success", "arguments": "", "status": "SUCCESS", "marker": "NXTEST: OPTIONS_EMPTY", "text": None},
        {"name": "return-aborted", "arguments": "nextcore-child-error", "status": "ABORTED", "marker": "NXTEST: OPTIONS_OK", "text": None},
        *[{"name": "exit-" + kind, "arguments": "nextcore-child-exit-" + kind, "status": "ABORTED",
           "marker": "NXTEST: EXPLICIT_EXIT kind=" + kind, "text": text, "binary_bytes": suffix}
          for kind, text, suffix in (("text", "authored failure", 0), ("empty", None, 0), ("blank", "", 0),
                                    ("controls", CONTROLS, 0), ("long", "L" * 1536, 0),
                                    ("binary", "authored failure", 3))],
    ]


def validate_log(raw, case):
    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw.decode("utf-8")).splitlines()
    expected = ["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED", "NEXTCORE: IMAGE_START", "NXTEST: EFI_ENTRY", case["marker"]]
    if case["text"] is None:
        expected.append("NEXTCORE: IMAGE_EXIT_DATA bytes=0 copied=0 pointer=null")
        require(not any(line.startswith("NEXTCORE: IMAGE_EXIT_TEXT ") for line in lines), "unexpected exit text")
    else:
        payload = case["text"].encode("utf-16-le") + b"\0\0"
        size = len(payload) + case["binary_bytes"]
        copied = min(size, 2048)
        units = min(len(payload) // 2 - 1, copied // 2)
        terminated = len(payload) <= copied
        expected += [
            f"NEXTCORE: IMAGE_EXIT_DATA bytes={size} copied={copied} units={units} terminated={str(terminated).lower()} truncated={str(size > copied).lower()} trailing_bytes={case['binary_bytes'] if terminated else 0}",
            'NEXTCORE: IMAGE_EXIT_TEXT text="' + escape_utf16(case["text"][:units]) + '"',
            "NEXTCORE: IMAGE_EXIT_DATA_FREE status=SUCCESS",
        ]
    expected.append("NEXTCORE: IMAGE_RETURN status=" + case["status"])
    positions = []
    for marker in expected:
        require(lines.count(marker) == 1, "missing/duplicate expected marker: " + marker[:180])
        positions.append(lines.index(marker))
    require(positions == sorted(positions), "marker order mismatch")
    require([line for line in lines if line.startswith("NEXTCORE: IMAGE_RETURN ")] == [expected[-1]], "exit text forged a return marker")
    require(not any("EXIT_UNEXPECTED_RETURN" in line or "IMAGE_CLEANUP_ERROR" in line for line in lines), "child Exit/loader cleanup failure")
    return {"expected_markers": expected, "ordered_exact_markers": True, "return_status_preserved": True,
            "text_escape_verified": case["text"] is not None, "returned_pool_freed": case["text"] is not None}


def validate_qemu_observation(receipt):
    require(receipt["cleanup_complete"] and not receipt["process_group_remaining"]
            and not receipt["adopted_children_remaining"], "QEMU cleanup incomplete")
    natural = receipt["natural_returncode"]
    if natural is not None:
        require(natural == 0 and receipt["returncode"] == 0
                and not receipt["stopped_by_harness"] and not receipt["timed_out"],
                "QEMU unexpected natural exit/crash")
    else:
        # QEMU normally handles SIGTERM and returns zero; SIGKILL/uncaught
        # SIGTERM are also valid only after this harness's intended deadline stop.
        require(receipt["stopped_by_harness"] and receipt["timed_out"]
                and receipt["returncode"] in (0, -signal.SIGTERM, -signal.SIGKILL),
                "QEMU unexpected exit during observation stop")


def finalize_report(report, before, deadline, output, started, expected_input_count):
    after, errors = {}, {}
    for path in before:
        try:
            after[path] = sha256(path, deadline)
        except Exception as error:
            # An expired deadline/read failure is missing integrity evidence,
            # never evidence of mutation and never a reason to lose the receipt.
            errors[path] = f"{type(error).__name__}: {error}"
    report["input_sha256_after"] = after
    report["input_hash_observation_errors"] = errors
    report["original_inputs_preserved"] = len(before) == expected_input_count and not errors and before == after
    report["elapsed_seconds"] = round(time.monotonic() - started, 4)
    report["deadline_exceeded"] = time.monotonic() > deadline
    report["passed"] = (len(report["cases"]) == len(cases()) and all(case["passed"] for case in report["cases"])
                        and report["original_inputs_preserved"] and "failure" not in report and not report["deadline_exceeded"])
    atomic_json(output / "report.json", report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--efi", type=Path, required=True)
    parser.add_argument("--child", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    args = parser.parse_args()
    enable_subreaper()
    output = args.output.resolve()
    require(not output.exists() and "," not in str(output), "output must be a fresh comma-free directory")
    inputs = {key: getattr(args, key).resolve(strict=True) for key in ("efi", "child", "ovmf_code", "ovmf_vars")}
    require(all(path.is_file() and "," not in str(path) for path in inputs.values()), "inputs must be comma-free regular files")
    output.mkdir(parents=True)
    started, deadline = time.monotonic(), time.monotonic() + 90
    before = {}
    report = dict(schema="nextcore.exit-data.ovmf.v1", layer="UEFI StartImage/Exit diagnostic data", cases=[],
                  input_sha256_before=before, xnu_executed=False, macos_boot_verified=False, metal_verified=False)
    try:
        for path in inputs.values():
            before[str(path)] = sha256(path, deadline)
        for case in cases():
            directory = output / case["name"]
            esp = directory / "esp"
            boot, oc = esp / "EFI/BOOT", esp / "EFI/OC"
            boot.mkdir(parents=True)
            oc.mkdir()
            copies = {"efi": boot / "BOOTX64.EFI", "child": boot / "NXTEST.EFI", "ovmf_vars": directory / "vars.fd"}
            for key, destination in copies.items():
                shutil.copyfile(inputs[key], destination)
                require(sha256(destination, deadline) == before[str(inputs[key])], "copy hash mismatch")
            config = plistlib.dumps({"Misc": {"Entries": [{"Enabled": True, "Path": "\\EFI\\BOOT\\NXTEST.EFI", "Arguments": case["arguments"]}]}}, fmt=plistlib.FMT_XML)
            (oc / "config.plist").write_bytes(config)
            serial = directory / "serial.log"
            command = [args.qemu, "-machine", "q35,accel=tcg,smm=off", "-cpu", "Nehalem", "-m", "256", "-smp", "1",
                       "-display", "none", "-monitor", "none", "-serial", f"file:{serial}", "-net", "none", "-no-reboot",
                       "-drive", f"if=pflash,format=raw,readonly=on,file={inputs['ovmf_code']}",
                       "-drive", f"if=pflash,format=raw,file={copies['ovmf_vars']}",
                       "-drive", f"format=raw,file=fat:rw:{esp}"]
            atomic_json(directory / "command.json", command)
            result = dict(name=case["name"], passed=False)
            report["cases"].append(result)
            result["qemu"] = run_bounded(command, directory / "stdout.log", directory / "stderr.log", deadline, limit=8)
            try:
                validate_qemu_observation(result["qemu"])
                raw = read_bounded(serial, deadline=deadline)
                result.update(validate_log(raw, case))
                result["serial_sha256"] = sha256(serial, deadline)
                result["copied_images_unchanged"] = all(sha256(copies[key], deadline) == before[str(inputs[key])] for key in ("efi", "child"))
                result["passed"] = result["copied_images_unchanged"]
            except Exception as error:
                result["failure"] = str(error)
            print(json.dumps({"name": result["name"], "passed": result["passed"], "failure": result.get("failure")}), flush=True)
    except Exception as error:
        report["failure"] = str(error)
    finally:
        finalize_report(report, before, deadline, output, started, len(inputs))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
