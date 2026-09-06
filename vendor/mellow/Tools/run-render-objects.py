#!/usr/bin/env python3
"""MSL render objects -> real GL GPU -> independent triangle/gradient pixel checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import secrets
import shutil
import struct
import subprocess
import sys
import zlib

WIDTH, HEIGHT, FRAME_BYTES = 64, 48, 64 * 48 * 4
NEGATIVES = {
    "read_before_gpu", "zero_texture", "wrong_function_stage", "null_function", "swapped_stages",
    "empty_commit", "present_before_encoding", "wait_before_completion", "null_attachment",
    "nonfinite_clear", "abandoned_encoder", "commit_active_encoder", "draw_without_pipeline",
    "null_pipeline", "end_empty_encoder", "nonfinite_parameters", "unsupported_primitive",
    "unsafe_vertex_start", "unsafe_vertex_count", "foreign_texture", "foreign_function",
    "foreign_pipeline", "second_draw_in_pass", "duplicate_end_encoding", "ended_encoder_mutation",
    "duplicate_present", "pass_after_present",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError("Duplicate JSON key: " + key)
            out[key] = value
        return out
    def invalid(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def parameters(seed, iteration):
    r = (seed + iteration * 0x9E3779B9) & 0xFFFFFFFF
    return (f32(((r & 15) - 7) * f32(.005)),
            f32((((r >> 4) & 15) - 7) * f32(.005)),
            f32(((r >> 8) & 255) / 255.), f32(1. / 64.))


def triangle(seed, iteration):
    params = parameters(seed, iteration)
    points = [((f32(f32(x) + params[0]) + 1.) * WIDTH / 2.,
               (1. - f32(f32(y) + params[1])) * HEIGHT / 2.)
              for x, y in ((-.72, -.52), (.58, -.32), (-.18, .72))]
    def edge(a, b, x, y):
        return (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
    sign = 1 if edge(points[0], points[1], *points[2]) > 0 else -1
    lines = []
    lengths = []
    for a, b in zip(points, points[1:] + points[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        lines.append((-dy * sign, dx * sign, (dy * a[0] - dx * a[1]) * sign))
        lengths.append(math.hypot(dx, dy))
    # Edge-function units are pixels squared. This bounds only the subpixel
    # strip adjacent to the triangle, never arbitrary pixels along infinite lines.
    return params, lines, max(lengths) / 256.


def pixel_contract(seed, iteration, x, y):
    params, edges, tolerance = triangle(seed, iteration)
    signed = [a * (x + .5) + b * (y + .5) + c for a, b, c in edges]
    kind = "outside" if min(signed) < -tolerance else "inside" if min(signed) > tolerance else "boundary"
    color = (round((x + .5) * params[3] * 255), round((y + .5) * params[3] * 255),
             round(params[2] * 255), 255)
    return kind, color


def verify_stream(path, seed, count):
    summary = dict(passed=False, frames_verified=0, pixels_verified=0, boundary_pixels=0,
                   boundary_foreground_pixels=0, foreground_pixels=0, minimum_foreground_per_frame=None,
                   rgb_tolerance=1, alpha_tolerance=0, edge_tolerance="max_triangle_edge_length/256 in edge-function units",
                   first_failure=None, raw_stream_sha256=None)
    if not path.is_file() or path.stat().st_size != count * FRAME_BYTES:
        summary["first_failure"] = {"reason": "Raw stream length does not equal frame count * 64 * 48 * 4"}
        return summary
    sha = hashlib.sha256()
    with path.open("rb") as raw:
        for i in range(count):
            rgba = raw.read(FRAME_BYTES)
            sha.update(rgba)
            params, edges, tolerance = triangle(seed, i)
            blue = round(params[2] * 255)
            foreground = 0
            for y in range(HEIGHT):
                green = round((y + .5) * params[3] * 255)
                for x in range(WIDTH):
                    at = (y * WIDTH + x) * 4
                    actual = tuple(rgba[at:at + 4])
                    signed = [a * (x + .5) + b * (y + .5) + c for a, b, c in edges]
                    minimum = min(signed)
                    kind = "outside" if minimum < -tolerance else "inside" if minimum > tolerance else "boundary"
                    expected = (round((x + .5) * params[3] * 255), green, blue, 255)
                    clear = actual == (0, 0, 0, 0)
                    triangle_color = actual[3] == 255 and all(abs(actual[c] - expected[c]) <= 1 for c in range(3))
                    valid = clear if kind == "outside" else triangle_color if kind == "inside" else clear or triangle_color
                    if not valid:
                        summary["first_failure"] = dict(frame=i, x=x, y=y, classification=kind, actual=list(actual),
                                                        triangle_color=list(expected), signed_edges=signed, edge_tolerance=tolerance)
                        return summary
                    if kind == "boundary":
                        summary["boundary_pixels"] += 1
                        if triangle_color:
                            summary["boundary_foreground_pixels"] += 1
                    if triangle_color:
                        foreground += 1
                    summary["pixels_verified"] += 1
            if not foreground:
                summary["first_failure"] = dict(frame=i, reason="Frame contains no rendered foreground")
                return summary
            summary["foreground_pixels"] += foreground
            previous = summary["minimum_foreground_per_frame"]
            summary["minimum_foreground_per_frame"] = foreground if previous is None else min(previous, foreground)
            summary["frames_verified"] += 1
    summary.update(passed=True, raw_stream_sha256=sha.hexdigest())
    return summary


def validate_native(native, seed, count, visible, raw_path):
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    if type(native) is not dict:
        return ["Native result must be an object"]
    need("error" not in native, "Conflicting successful report contains an error")
    for key, expected in (("schema_version", 1), ("seed", seed), ("requested_frames", count), ("frames_completed", count),
                          ("width", WIDTH), ("height", HEIGHT), ("first_sequence", 1), ("last_sequence", count),
                          ("epoch", 1), ("pipeline_build_count", 1), ("msl_stages_translated", 2), ("native_program_compilations", 1)):
        need(type(native.get(key)) is int and native[key] == expected, key + " mismatch")
    for key in ("passed", "portable_mellow_object_api", "all_frame_completions_correlated"):
        need(native.get(key) is True, key + " must be true")
    for key in ("apple_metal_abi_registered", "native_macos_execution", "windowserver_acceleration_verified",
                "display_scanout_verified", "runtime_received_pixel_oracle"):
        need(native.get(key) is False, key + " must be false")
    need(native.get("visible_requested") is visible and native.get("row_origin") == "top-left", "Presentation/row-origin mismatch")
    negatives = native.get("negative_checks")
    need(type(negatives) is list and all(type(value) is str for value in negatives) and
         len(negatives) == len(NEGATIVES) and set(negatives) == NEGATIVES, "Negative API coverage mismatch")
    need(type(native.get("checks")) is int and native["checks"] >= 15 * count + 30, "Insufficient object assertions")
    device = native.get("device")
    if type(device) is not dict:
        errors.append("Missing hardware-driver identity")
    else:
        for key in ("vendor", "renderer", "version", "glsl_version"):
            need(type(device.get(key)) is str and 0 < len(device[key]) < 16384, "Invalid device " + key)
        for key in ("accelerated_pixel_format", "core_profile", "software_renderer_rejected"):
            need(device.get(key) is True, "Driver " + key + " missing")
        major, minor = device.get("major"), device.get("minor")
        need(type(major) is int and type(minor) is int and (major > 3 or major == 3 and minor >= 3), "GL3.3 core required")
    if not raw_path.is_file() or raw_path.stat().st_size != count * FRAME_BYTES:
        errors.append("Missing or wrong-size native RGBA stream")
        return errors
    need(native.get("raw_stream_sha256") == digest(raw_path), "Native raw stream hash mismatch")
    indices = [0] if count == 1 else [0, count - 1]
    samples = native.get("samples")
    if type(samples) is not list or len(samples) != len(indices):
        errors.append("Missing bounded sample events")
    else:
        with raw_path.open("rb") as stream:
            for sample, i in zip(samples, indices):
                if type(sample) is not dict:
                    errors.append("Malformed sample event")
                    continue
                for key, value in (("iteration", i), ("sequence", i + 1), ("texture_sequence", i + 1), ("epoch", 1)):
                    need(type(sample.get(key)) is int and sample[key] == value, "Sample " + key + " mismatch")
                for key in ("render_submitted", "fence_signaled", "readback_completed", "resources_released"):
                    need(sample.get(key) is True, "Sample " + key + " incomplete")
                need(sample.get("swap_completed") is visible and sample.get("scanout_verified") is False, "Sample swap/scanout scope mismatch")
                stream.seek(i * FRAME_BYTES)
                need(sample.get("rgba_sha256") == hashlib.sha256(stream.read(FRAME_BYTES)).hexdigest(), "Sample raw RGBA hash mismatch")
    return errors


def write_snapshot(path, rgba):
    """Lossless encoding of actual GPU RGBA bytes; no reference pixels are used."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    rows = b"".join(b"\0" + rgba[y * WIDTH * 4:(y + 1) * WIDTH * 4] for y in range(HEIGHT))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 6, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cxx", default=shutil.which("g++") or shutil.which("clang++"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--frames", type=int, default=1000)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    if not args.cxx:
        parser.error("A native C++17 compiler is required")
    if not 1 <= args.frames <= 10000 or not 1 <= args.timeout <= 180:
        parser.error("Frames must be 1-10000; timeout 1-180 seconds")
    if args.visible and not args.render:
        parser.error("--visible requires --render")
    root = Path(__file__).resolve().parents[1]
    args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=True)
    sources = ["Runtime/RenderObjects.hpp", "Runtime/RenderObjects.cpp", "Runtime/RenderShaderJit.hpp", "Runtime/RenderShaderJit.cpp",
               "Runtime/OpenGLProvider.hpp", "Runtime/OpenGLProvider.cpp", "Runtime/MetalObjects.hpp",
               "Runtime/OpenCLProvider.hpp", "Runtime/PlatformRuntime.hpp", "Runtime/ShaderJit.hpp",
               "tests/render_fixture.hpp", "tests/render_objects_gpu_tests.cpp", "tests/opencl_runtime_sha256.hpp",
               "Tools/run-render-objects.py"]
    report = dict(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                  scope="portable-Mellow-MSL-render-objects-native-Windows-OpenGL-GPU",
                  os=dict(system=platform.system(), release=platform.release(), version=platform.version()),
                  source_sha256={name: digest(root / name) for name in sources}, requested_frames=args.frames,
                  visible_requested=args.visible, gpu_work_executed=False, passed=False, status="FAILED",
                  apple_metal_abi_registered=False, native_macos_execution=False, windowserver_acceleration_verified=False,
                  display_scanout_verified=False, fixture_origin="original MSL source, not Apple-produced AIR")
    options = {"env": os.environ.copy()}
    if os.name == "nt":
        compiler = Path(shutil.which(args.cxx) or args.cxx).resolve()
        options["env"]["PATH"] = str(compiler.parent) + os.pathsep + options["env"].get("PATH", "")
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    started = False
    try:
        version = subprocess.run([args.cxx, "--version"], capture_output=True, text=True, timeout=20, **options)
        report["compiler_version"] = version.stdout.strip()
        executable = args.out / ("render-objects.exe" if os.name == "nt" else "render-objects")
        command = [args.cxx, "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic",
                   *[str(root / name) for name in ("Runtime/OpenGLProvider.cpp", "Runtime/RenderShaderJit.cpp",
                                                  "Runtime/RenderObjects.cpp", "tests/render_objects_gpu_tests.cpp")],
                   "-o", str(executable)]
        command += ["-lopengl32", "-lgdi32", "-luser32", "-static-libgcc", "-static-libstdc++"] if os.name == "nt" else ["-pthread"]
        build = subprocess.run(command, capture_output=True, text=True, timeout=120, **options)
        report["build"] = dict(exit_code=build.returncode, stdout=build.stdout, stderr=build.stderr)
        if build.returncode:
            print(build.stdout + build.stderr, file=sys.stderr)
            return 1
        report["binary_sha256"] = digest(executable)
        if not args.render:
            report["status"] = "BUILT_ONLY"
            return 0
        if os.name != "nt":
            report.update(status="NOT_AVAILABLE", error="Actual native OpenGL provider is Windows WGL only")
            return 1
        token = secrets.token_hex(8)
        result_path, raw_path = args.out / (token + ".json"), args.out / (token + ".rgba")
        seed = secrets.randbits(32)
        report["seed"] = seed
        invocation = [str(executable), "--render", "--report", str(result_path), "--raw", str(raw_path),
                      "--seed", str(seed), "--frames", str(args.frames)]
        if args.visible:
            invocation.append("--visible")
        started = True
        worker = subprocess.run(invocation, capture_output=True, text=True, timeout=args.timeout, **options)
        report["worker"] = dict(exit_code=worker.returncode, stdout=worker.stdout, stderr=worker.stderr)
        print(worker.stdout, end="")
        if not result_path.is_file():
            raise ValueError("Worker produced no current report; GPU execution unknown")
        native = strict_json(result_path.read_text(encoding="utf-8"))
        if type(native) is not dict:
            raise ValueError("Worker report is not an object")
        report["native"] = native
        report["gpu_work_executed"] = True if type(native.get("frames_completed")) is int and native["frames_completed"] > 0 else None
        result_path.replace(args.out / "render-objects-native.json")
        report["validation_errors"] = validate_native(native, seed, args.frames, args.visible, raw_path)
        oracle = verify_stream(raw_path, seed, args.frames)
        report["independent_pixel_reference"] = oracle
        if raw_path.is_file():
            raw_path.replace(args.out / "actual-gpu-frames.rgba")
            report["raw_stream_file"] = "actual-gpu-frames.rgba"
            report["raw_stream_sha256"] = digest(args.out / "actual-gpu-frames.rgba")
            if oracle["passed"]:
                with (args.out / "actual-gpu-frames.rgba").open("rb") as stream:
                    stream.seek((args.frames - 1) * FRAME_BYTES)
                    write_snapshot(args.out / "actual-gpu-last-frame.png", stream.read(FRAME_BYTES))
                report["snapshot_file"] = "actual-gpu-last-frame.png"
                report["snapshot_sha256"] = digest(args.out / "actual-gpu-last-frame.png")
        report["source_changed_during_run"] = [name for name in sources if digest(root / name) != report["source_sha256"][name]]
        passed = worker.returncode == 0 and not report["validation_errors"] and oracle["passed"] and not report["source_changed_during_run"]
        report.update(passed=passed, status="PASS_MSL_RENDER_OBJECTS_GPU" if passed else "FAILED")
        return 0 if passed else 1
    except subprocess.TimeoutExpired as failure:
        report.update(status="TIMED_OUT", error=f"Worker/compiler deadline {failure.timeout} seconds exceeded",
                      gpu_work_executed=None if started else False)
        return 1
    except (OSError, ValueError, KeyError) as failure:
        report["error"] = str(failure)
        if started and "native" not in report:
            report["gpu_work_executed"] = None
        return 1
    finally:
        report["source_changed_during_run"] = [name for name in sources if not (root / name).is_file() or
                                               digest(root / name) != report["source_sha256"][name]]
        if report["source_changed_during_run"]:
            report.update(passed=False, status="FAILED_SOURCE_CHANGED")
        destination = args.out / "render-objects.json"
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("Report:", destination)
        if report["source_changed_during_run"]:
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
