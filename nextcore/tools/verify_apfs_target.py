#!/usr/bin/env python3
"""Authored SFS-forwarding fixture for explicit NextCore APFS target selection."""
import argparse
import json
from pathlib import Path
import re
import sys

import verify_apfs_jumpstart as vm
import verify_hal_ovmf as bounded

CASES = ("success", "child-error", "missing-label", "duplicate-label", "missing-file", "feature-disabled", "own-filesystem")
MARKER = b"NEXTCORE_FIXTURE_CHILDREN=1"


def fixture_copy(application, children):
    driver, changes = vm.authored_driver(application)
    vm.require(children in (1, 2), "authored child count")
    vm.require(driver.count(MARKER) == 1, "fixture selector literal must be unique")
    if children == 2:
        offset = driver.index(MARKER) + len(MARKER) - 1
        copy = bytearray(driver)
        copy[offset] = ord("2")
        driver = bytes(copy)
        changes.append({"offset": offset, "before": ord("1"), "after": ord("2")})
    return driver, changes


def validate_serial(raw, case, size):
    vm.require(case in CASES, "unknown target case")
    vm.require(len(raw) <= vm.MAX_SERIAL, "serial exceeds cap")
    lines = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw.decode("utf-8", "strict")).splitlines()
    def once(marker):
        vm.require(lines.count(marker) == 1, f"missing/duplicate {marker}")
        return lines.index(marker)
    def ordered(markers):
        positions = [once(marker) for marker in markers]
        vm.require(positions == sorted(positions), "marker order")
        return positions
    base = ordered(["NEXTCORE: EFI_ENTRY", "NEXTCORE: CONFIG_PARSED"])[-1]
    if case in ("success", "own-filesystem"):
        count = 2 if case == "own-filesystem" else 1
        picker = ordered([f"NEXTCORE: PICKER_BEGIN entries={count}",
                          "NEXTCORE: PICKER_READY renderer=GOP selected=0", "NEXTCORE: PICKER_BOOT index=0"])
        vm.require(base < picker[0], "picker before configuration")
        base = picker[-1]
    else:
        vm.require(not any(line.startswith("NEXTCORE: PICKER_") for line in lines), "unexpected picker")
    forbidden = ("NXFSFIX: PUBLISH_ERROR", "NEXTCORE: IMAGE_CLEANUP_ERROR", "NXTEST: OPTIONS_INVALID",
                 "NEXTCORE: IMAGE_OPTIONS_ERROR", "NEXTCORE: CONSOLE_ERROR", "NEXTCORE: CONSOLE_RETAINED",
                 "NEXTCORE: CONFIG_ERROR", "NEXTCORE: CONFIG_INVALID", "NEXTCORE: PICKER_ERROR",
                 "NEXTCORE: TARGET_REJECTED", "NXAPFS: EXTRACT_ERROR", "NXAPFS: NOT_BOOT_DRIVER",
                 "NXAPFS: START_REJECT_CLEANUP", "NXAPFS: LOAD_REJECT_CLEANUP")
    vm.require(not any(any(value in line for value in forbidden) for line in lines), "fixture/cleanup failure")
    failure = case in ("feature-disabled", "missing-label", "duplicate-label", "missing-file")
    status = ("UNSUPPORTED" if case == "feature-disabled" else "NO_MAPPING" if case == "duplicate-label"
              else "NOT_FOUND" if failure else "ABORTED" if case == "child-error" else "SUCCESS")
    returns = [line for line in lines if line.startswith("NEXTCORE: IMAGE_RETURN")]
    errors = [line for line in lines if line.startswith("NEXTCORE: IMAGE_LOAD_ERROR")]
    vm.require(returns == ([] if failure else [f"NEXTCORE: IMAGE_RETURN status={status}"])
               and errors == ([f"NEXTCORE: IMAGE_LOAD_ERROR status={status}"] if failure else []),
               "conflicting/missing/duplicate terminal outcome")
    if failure:
        vm.require(not any(line.startswith(("NXTEST:", "NEXTCORE: CONSOLE_")) for line in lines)
                   and "NEXTCORE: IMAGE_START" not in lines, "rejected target entered application lifecycle")
    if case == "feature-disabled":
        disabled = ordered(["NEXTCORE: APFS_TARGET_UNSUPPORTED feature=disabled", "NEXTCORE: IMAGE_LOAD_ERROR status=UNSUPPORTED"])
        vm.require(base < disabled[0] and "NEXTCORE: IMAGE_LOAD_BEGIN" not in lines
                   and "NEXTCORE: APFS_TARGET_BEGIN" not in lines, "disabled feature began loading")
        vm.require(not any(line.startswith(("NXAPFS:", "NXFSFIX:", "NXTEST:")) for line in lines), "disabled feature executed child")
        return {"status": "UNSUPPORTED", "driver_entered": False, "target_entered": False, "apfs_semantics_verified": False}
    if case == "own-filesystem":
        vm.require(not any(line.startswith(("NXAPFS:", "NXFSFIX:", "NEXTCORE: APFS_")) for line in lines), "unselected APFS entry executed")
    else:
        start = once("NEXTCORE: APFS_TARGET_BEGIN")
        vm.require(base < start, "APFS preparation before configuration/picker selection")
        count = 2 if case == "duplicate-label" else 1
        driver = ordered([f"NXAPFS: EXTRACT_OK bytes={size} block_size=4096 extents=2 readback=true",
                 "NXAPFS: DRIVER_START", "NXAPFS: DRIVER_RETURN status=SUCCESS",
                 "NXAPFS: DRIVER_RESIDENT", "NXAPFS: CONNECT status=SUCCESS"])
        ordered(["NXAPFS: DRIVER_START", "NXFSFIX: EFI_ENTRY", f"NXFSFIX: BINDING_READY children={count}",
                 f"NXFSFIX: BIND_START children={count}"]
                + [f"NXFSFIX: CHILD index={i} published=true" for i in range(count)]
                + ["NXAPFS: CONNECT status=SUCCESS"])
        vm.require(start < driver[0], "extraction before selected entry")
        labels = [line for line in lines if line.startswith("NEXTCORE: APFS_LABEL ")]
        matched = case != "missing-label"
        vm.require(labels == [f"NEXTCORE: APFS_LABEL index={i} matched={str(matched).lower()} open=true close=Some(SUCCESS) protocol_close=Some(SUCCESS) status=SUCCESS"
                              for i in range(count)], "label/open/close gate")
        selections = [line for line in lines if line.startswith("NEXTCORE: APFS_SELECT ")]
        vm.require(len(selections) == 1, "missing/duplicate selection summary")
        select = re.fullmatch(r"NEXTCORE: APFS_SELECT examined=(\d+) candidates=(\d+) matches=(\d+) metadata_bytes=(\d+) status=(\w+)", selections[0])
        vm.require(select is not None, "invalid selection summary")
        examined, candidates, matches, metadata = map(int, select.groups()[:4])
        expected_status = "NO_MAPPING" if count == 2 else "NOT_FOUND" if case == "missing-label" else "SUCCESS"
        vm.require(examined == count + 1 and candidates == count and matches == (count if matched else 0)
                   and 0 < metadata <= 1024*1024 and select[5] == expected_status, "wrong selection scope/outcome")
        selection = ordered(["NXAPFS: CONNECT status=SUCCESS"] + labels + selections)[-1]
        base = selection
        if case in ("missing-label", "duplicate-label", "missing-file"):
            vm.require(lines.count("NEXTCORE: IMAGE_LOAD_BEGIN") == (1 if case == "missing-file" else 0), "unexpected target LoadImage")
            terminal = ordered((["NEXTCORE: IMAGE_LOAD_BEGIN"] if case == "missing-file" else [])
                               + [f"NEXTCORE: IMAGE_LOAD_ERROR status={status}"])
            vm.require(base < terminal[0], "target load/error before selection")
            return {"status": status, "driver_entered": True, "target_entered": False, "apfs_semantics_verified": False}
    lifecycle = ordered(["NEXTCORE: IMAGE_LOAD_BEGIN", "NEXTCORE: IMAGE_START", "NXTEST: EFI_ENTRY",
                         "NXTEST: OPTIONS_OK", "NEXTCORE: CONSOLE_UNINSTALL status=SUCCESS",
                         "NEXTCORE: CONSOLE_RELEASE reused=false removed=true storage_freed=true",
                         f"NEXTCORE: IMAGE_RETURN status={status}"])
    vm.require(base < lifecycle[0], "target LoadImage before selection/configuration")
    vm.require(len([line for line in lines if line.startswith("NEXTCORE: CONSOLE_RELEASE")]) == 1
               and len([line for line in lines if line.startswith("NEXTCORE: CONSOLE_UNINSTALL")]) == 1,
               "conflicting console cleanup")
    vm.require(len([line for line in lines if line.startswith("NXTEST:")]) == 2, "unexpected target output")
    return {"status": status, "driver_entered": case != "own-filesystem", "target_entered": True,
            "load_options_verified": True, "console_cleanup": True, "apfs_semantics_verified": False}


def config(case):
    entry = {"Name": "NextCore authored APFS target", "Enabled": True,
             "Path": "\\EFI\\OC\\missing.efi" if case == "missing-file" else "\\EFI\\OC\\NXTEST.efi",
             "Arguments": "nextcore-child-error" if case == "child-error" else "nextcore-child-success 한글",
             "ApfsVolume": "nxfstest" if case == "missing-label" else "NXFSTEST"}
    entries = [entry]
    if case == "own-filesystem":
        entry.pop("ApfsVolume")
        entry["Name"] = "NextCore authored own-volume target"
        entries.append({"Name": "Unselected APFS entry", "Enabled": True, "Path": "\\EFI\\OC\\missing.efi", "ApfsVolume": "Absent"})
    return {"Misc": {"Boot": {"ShowPicker": case in ("success", "own-filesystem")}, "Entries": entries}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("efi", "efi-no-apfs", "fixture", "child", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--qemu", type=Path, default=Path("/usr/bin/qemu-system-x86_64"))
    parser.add_argument("--ovmf-code", type=Path, default=Path("/usr/share/OVMF/OVMF_CODE_4M.fd"))
    parser.add_argument("--ovmf-vars", type=Path, default=Path("/usr/share/OVMF/OVMF_VARS_4M.fd"))
    parser.add_argument("--qemu-img", default="/usr/bin/qemu-img")
    parser.add_argument("--mkfs", default="/usr/sbin/mkfs.vfat")
    parser.add_argument("--mmd", default="/usr/bin/mmd")
    parser.add_argument("--mcopy", default="/usr/bin/mcopy")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--case", action="append", choices=CASES)
    args = parser.parse_args()
    vm.require(sys.platform == "linux" and 8 <= args.timeout <= 30, "Linux with 8..30-second guest bound required")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    bounded.enable_subreaper()
    bounded.child_limits = vm.limits
    report = {"passed": False, "cases": [], "apfs_filesystem_implementation": False, "argv": sys.argv}
    try:
        inputs = {name: getattr(args,name).resolve(strict=True) for name in ("efi", "efi_no_apfs", "fixture", "child", "qemu", "ovmf_code", "ovmf_vars")}
        inputs.update({name: Path(getattr(args,name)).resolve(strict=True) for name in ("qemu_img", "mkfs", "mmd", "mcopy")})
        inputs.update({"target_harness": Path(__file__).resolve(), "harness": Path(vm.__file__).resolve(), "process_helper": Path(bounded.__file__).resolve()})
        inputs["efi_enabled"] = inputs["efi"]
        application = bounded.read_bounded(inputs["fixture"], vm.PARTITION_BYTES//2)
        for case in args.case or CASES:
            driver, changes = fixture_copy(application, 2 if case == "duplicate-label" else 1)
            copy = out / f"{case}-driver.efi"
            copy.write_bytes(driver)
            selected_inputs = dict(inputs)
            selected_inputs["efi"] = inputs["efi_no_apfs"] if case == "feature-disabled" else inputs["efi"]
            selected_inputs["probe"] = inputs["fixture"]
            selected_inputs["driver_copy"] = copy
            custom = {"payload": driver, "volume_label": "NXFSTEST", "config": config(case), "validator": validate_serial,
                      "picker": case in ("success", "own-filesystem"),
                      "files": {"TARGET": (inputs["child"], "::/EFI/OC/NXTEST.efi")}}
            result = vm.run_case(args, case, selected_inputs, application, driver, out/case, custom)
            item = {"case": case, "passed": result["passed"], "driver_changes": changes,
                    "driver_sha256": vm.digest(driver), "report": f"{case}/report.json"}
            report["cases"].append(item)
            print(json.dumps(item), flush=True)
        report["passed"] = all(item["passed"] for item in report["cases"])
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        bounded.atomic_json(out/"report.json", report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
