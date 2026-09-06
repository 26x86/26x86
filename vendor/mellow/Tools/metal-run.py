#!/usr/bin/env python3
"""Compile/run the real macOS Metal probe with a process deadline and JSON report."""
import argparse
import hashlib
import json
import platform
import re
import struct
import subprocess
import time
from pathlib import Path

EXPECTED_RENDER_SHA256 = "7f8f467143b62cef24e8b429a733a6b2fbf67d6a828dd02f74d7353bce78d6fb"


def challenge_vectors(nonce, count):
    input_state = nonce ^ 0xC001D00D
    poison_state = nonce ^ 0x51A7E5ED
    inputs, poison, expected = [], [], []
    for index in range(count):
        input_state = (input_state * 1664525 + 1013904223) & 0xFFFFFFFF
        value = index + 1 if index < 4 else input_state ^ index
        poison_state = (poison_state * 1664525 + 1013904223) & 0xFFFFFFFF
        poisoned = poison_state ^ ((index * 0x9E3779B9) & 0xFFFFFFFF)
        inputs.append(value)
        poison.append(poisoned)
        expected.append((value * 7 + 3) & 0xFFFFFFFF)
    return inputs, poison, expected


def words_sha256(values):
    return hashlib.sha256(struct.pack(f"<{len(values)}I", *values)).hexdigest()


def valid_gpu_times(event):
    start, end = event.get("gpu_start_time"), event.get("gpu_end_time")
    return (type(start) in (float, int) and type(end) in (float, int) and
            start > 0 and end >= start and event.get("gpu_timing_recorded") is True)


def evaluate_events(events, registry_id=None):
    if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
        return False, "invalid_event_container"
    if any(e.get("stage") == "failed" for e in events):
        return False, "probe_reported_failure"
    stages = [e.get("stage") for e in events]
    if registry_id is None:
        return False, "enumeration_only_is_not_acceleration"
    required = ["target_correlated", "challenge_initialized", "compute_output_passed",
                "render_output_passed", "completed"]
    if any(stages.count(name) != 1 for name in required):
        return False, "missing_or_duplicated_evidence_stage"
    positions = [stages.index(name) for name in required]
    if positions != sorted(positions) or stages[-1] != "completed":
        return False, "invalid_evidence_order"
    evidence = {e["stage"]: e for e in events if e.get("stage") in required}
    if any(e.get("schema_version") != 3 for e in evidence.values()):
        return False, "unsupported_evidence_schema"
    physical, challenge = evidence["target_correlated"], evidence["challenge_initialized"]
    compute, render, final = (evidence[name] for name in required[2:])
    try:
        wanted = int(registry_id, 0) if isinstance(registry_id, str) else int(registry_id)
    except (ValueError, TypeError):
        return False, "invalid_requested_registry_id"
    if not 0 < wanted < 2 ** 64 or any(str(e.get("registry_id")) != str(wanted) for e in (physical, challenge, compute, render, final)):
        return False, "registry_id_mismatch"
    if (physical.get("physical_vendor"), physical.get("physical_device"), physical.get("physical_bdf")) != (0x8086, 0x7D41, 0x1000):
        return False, "wrong_physical_target"
    if (physical.get("visible_vendor") != 0x8086 or physical.get("visible_device") not in (0x7D41, 0x9A49) or
            physical.get("physical_identity_source") != "pci-config-before-spoof" or
            physical.get("unique_metal_registry_match") is not True or
            not isinstance(physical.get("device_name"), str) or
            any(marker in physical["device_name"].casefold() for marker in ("software", "swiftshader", "llvmpipe", "softpipe"))):
        return False, "target_attribution_incomplete"
    nonce = challenge.get("nonce")
    if type(nonce) is not int or not 0 < nonce < 2 ** 32 or nonce != compute.get("nonce") or challenge.get("count") != 4096 or compute.get("count") != 4096:
        return False, "challenge_mismatch"
    inputs, poison, wanted_output = challenge_vectors(nonce, 4096)
    input_hash, poison_hash, expected_hash = map(words_sha256, (inputs, poison, wanted_output))
    if (challenge.get("input_sha256") != input_hash or challenge.get("initial_output_sha256") != poison_hash or
            challenge.get("expected_output_sha256") != expected_hash or
            challenge.get("initial_nonce_witness") != (nonce ^ 0xDEADBEEF) or
            challenge.get("expected_nonce_witness") != (nonce ^ 0x7D410003) or
            challenge.get("acceptance_input_first_four") != [1, 2, 3, 4] or
            challenge.get("acceptance_output_first_four") != [10, 17, 24, 31]):
        return False, "challenge_hash_or_acceptance_vector_mismatch"
    actual = compute.get("actual_first_four")
    if (compute.get("mismatches") != 0 or actual != [10, 17, 24, 31] or
            compute.get("expected_first_four") != [10, 17, 24, 31]):
        return False, "computed_output_not_verified"
    hashes = (challenge.get("input_sha256"), challenge.get("initial_output_sha256"), compute.get("output_sha256"), render.get("readback_sha256"))
    if (any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None for value in hashes) or
            compute.get("output_sha256") != expected_hash or compute.get("expected_output_sha256") != expected_hash or
            poison_hash == expected_hash or compute.get("output_changed") is not True):
        return False, "output_unchanged_or_hash_missing"
    if (compute.get("nonce_witness") != (nonce ^ 0x7D410003) or
            compute.get("expected_nonce_witness") != (nonce ^ 0x7D410003) or
            str(compute.get("queue_registry_id")) != str(wanted) or
            str(compute.get("command_registry_id")) != str(wanted) or not valid_gpu_times(compute)):
        return False, "compute_device_or_gpu_timing_mismatch"
    if render.get("pixels") != 16 or render.get("mismatches") != 0 or render.get("actual_first_rgba") != [255, 0, 0, 255] or render.get("expected_rgba") != [255, 0, 0, 255]:
        return False, "render_output_not_verified"
    if (render.get("readback_sha256") != EXPECTED_RENDER_SHA256 or
            render.get("expected_readback_sha256") != EXPECTED_RENDER_SHA256 or
            str(render.get("command_registry_id")) != str(wanted) or not valid_gpu_times(render)):
        return False, "render_hash_device_or_gpu_timing_mismatch"
    if (final.get("compute_output_passed") is not True or
            final.get("render_output_passed") is not True or
            final.get("physical_identity_correlated") is not True or
            final.get("small_target_metal_probe_passed") is not True or final.get("cpu_fallback_used") is not False or
            final.get("full_metal_conformance_verified") is not False or final.get("windowserver_presentation_verified") is not False or
            final.get("hardware_irq_fence_verified") is not False or final.get("stress_acceptance_verified") is not False or
            final.get("evidence_scope") != "public Metal compute and offscreen render only"):
        return False, "final_evidence_invalid"
    return True, "small_compute_and_offscreen_render_only"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compute", help="Exact Metal registry ID returned by enumeration, e.g. 0x100001234")
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        parser.error("timeout must be in [1,300]")
    report = {"schema_version": 2, "host": platform.platform(), "native_probe_compiled": False,
              "small_target_metal_probe_passed": False, "full_metal_conformance_verified": False,
              "process_timeout": False, "events": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name("metal-probe.swift")
    report["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    result = 2
    try:
        if platform.system() != "Darwin":
            raise RuntimeError("Metal.framework is required; native probe not compiled/run on this host")
        executable = args.output.with_suffix(".probe")
        command = ["xcrun", "swiftc", "-swift-version", "5", "-O", str(source), "-o", str(executable),
                   "-framework", "Metal", "-framework", "IOKit", "-framework", "CryptoKit"]
        build = subprocess.run(command, capture_output=True, text=True, timeout=60)
        report["build"] = {"command": command, "returncode": build.returncode, "stderr": build.stderr}
        if build.returncode:
            raise RuntimeError("Native Swift/Metal compilation failed")
        report["native_probe_compiled"] = True
        report["probe_binary_sha256"] = hashlib.sha256(executable.read_bytes()).hexdigest()
        invocation = [str(executable)] + (["--compute", args.compute] if args.compute else [])
        started = time.monotonic()
        try:
            process = subprocess.run(invocation, capture_output=True, text=True, timeout=args.timeout)
            stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as error:
            report["process_timeout"] = True
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout
            stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
            returncode = None
        report["execution"] = {"command": invocation, "elapsed_seconds": time.monotonic() - started,
                               "returncode": returncode, "stderr": stderr}
        args.output.with_suffix(".jsonl").write_text(stdout, encoding="utf-8")
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    report["events"].append(event)
            except json.JSONDecodeError:
                report.setdefault("unparsed_stdout", []).append(line)
        accepted, reason = evaluate_events(report["events"], args.compute)
        if report.get("unparsed_stdout"):
            accepted, reason = False, "unparsed_probe_stdout"
        report["small_target_metal_probe_passed"] = accepted and returncode == 0 and not report["process_timeout"]
        report["assessment"] = reason if returncode == 0 else "probe_process_failed_or_did_not_exit"
        if report["process_timeout"]:
            report["assessment"] = "process_deadline_exceeded; terminating process does not guarantee GPU-command cancellation"
        result = 0 if report["small_target_metal_probe_passed"] else 2
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("events", "build", "execution")}, indent=2))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
