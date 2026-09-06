#!/usr/bin/env python3
"""Discover an installed OpenCL GPU substrate; opt-in fixed, bounded compute.

This bypasses Mellow Runtime/JIT/Metal. Driver-reported GPU identity is not a PCI
identity proof. All driver calls run in a worker process with a deadline.
"""
import argparse
import ctypes as ct
import ctypes.util
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import struct
import subprocess
import sys
import tempfile

CL_SUCCESS = 0
CL_DEVICE_NOT_FOUND = -1
CL_PLATFORM_NOT_FOUND_KHR = -1001
CL_DEVICE_TYPE_GPU = 4
CL_DEVICE_TYPE_CPU = 2
CL_QUEUE_PROFILING_ENABLE = 2
CL_MEM_READ_WRITE = 1
CL_MEM_COPY_HOST_PTR = 32
ELEMENTS = 256
REPETITIONS = 3
KERNEL = b"""__kernel void mellow_substrate(__global uint *values) {
    const size_t i = get_global_id(0);
    values[i] = values[i] * 7u + 3u;
}
"""


class OpenClError(RuntimeError):
    pass


def check(status, operation):
    if status != CL_SUCCESS:
        raise OpenClError(f"{operation}: OpenCL status {status}")


def base_report(compute):
    return {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "installed-host-opencl-substrate-only",
        "os": {"system": platform.system(), "release": platform.release(),
               "version": platform.version(), "machine": platform.machine(),
               "python_bits": ct.sizeof(ct.c_void_p) * 8},
        "compute_requested": compute,
        "status": "NOT_AVAILABLE",
        "platforms": [],
        "devices": [],
        "opencl_gpu_compute_pass": False,
        "mellow_runtime_used": False,
        "mellow_jit_used": False,
        "mellow_gpu_acceleration_pass": False,
        "metal_tested": False,
        "macos_driver_tested": False,
        "physical_pci_identity_verified": False,
        "identity_note": "GPU classification and names are reported by the installed OpenCL driver; no physical PCI mapping was established.",
    }


class OpenCL:
    def __init__(self):
        if sys.platform == "win32":
            self.path = "OpenCL.dll"
            self.lib = ct.WinDLL(self.path)
        elif sys.platform == "darwin":
            self.path = "/System/Library/Frameworks/OpenCL.framework/OpenCL"
            self.lib = ct.CDLL(self.path)
        else:
            self.path = ctypes.util.find_library("OpenCL") or "libOpenCL.so.1"
            self.lib = ct.CDLL(self.path)
        pointer, uint, integer, size = ct.c_void_p, ct.c_uint32, ct.c_int32, ct.c_size_t
        up, pp, sp, ip = ct.POINTER(uint), ct.POINTER(pointer), ct.POINTER(size), ct.POINTER(integer)
        self.bind("clGetPlatformIDs", integer, uint, pp, up)
        self.bind("clGetPlatformInfo", integer, pointer, uint, size, pointer, sp)
        self.bind("clGetDeviceIDs", integer, pointer, ct.c_uint64, uint, pp, up)
        self.bind("clGetDeviceInfo", integer, pointer, uint, size, pointer, sp)
        self.bind("clCreateContext", pointer, ct.POINTER(ct.c_ssize_t), uint, pp, pointer, pointer, ip)
        self.bind("clCreateCommandQueue", pointer, pointer, pointer, ct.c_uint64, ip)
        self.bind("clCreateProgramWithSource", pointer, pointer, uint, ct.POINTER(ct.c_char_p), sp, ip)
        self.bind("clBuildProgram", integer, pointer, uint, pp, ct.c_char_p, pointer, pointer)
        self.bind("clGetProgramBuildInfo", integer, pointer, pointer, uint, size, pointer, sp)
        self.bind("clCreateKernel", pointer, pointer, ct.c_char_p, ip)
        self.bind("clCreateBuffer", pointer, pointer, ct.c_uint64, size, pointer, ip)
        self.bind("clSetKernelArg", integer, pointer, uint, size, pointer)
        self.bind("clEnqueueNDRangeKernel", integer, pointer, pointer, uint, sp, sp, sp, uint, pp, pp)
        self.bind("clWaitForEvents", integer, uint, pp)
        self.bind("clGetEventProfilingInfo", integer, pointer, uint, size, pointer, sp)
        self.bind("clEnqueueReadBuffer", integer, pointer, pointer, uint, size, size, pointer, uint, pp, pp)
        self.bind("clFinish", integer, pointer)
        for name in ("clReleaseContext", "clReleaseCommandQueue", "clReleaseProgram",
                     "clReleaseKernel", "clReleaseMemObject", "clReleaseEvent"):
            self.bind(name, integer, pointer)

    def bind(self, name, result, *arguments):
        function = getattr(self.lib, name)
        function.restype = result
        function.argtypes = list(arguments)
        setattr(self, name, function)

    def text_info(self, function, handle, parameter):
        size = ct.c_size_t()
        check(function(handle, parameter, 0, None, ct.byref(size)), "query information size")
        if size.value > 1024 * 1024:
            raise OpenClError("Driver information string exceeds bounded size")
        value = ct.create_string_buffer(max(size.value, 1))
        check(function(handle, parameter, len(value), value, None), "query information")
        return value.value.decode("utf-8", errors="replace")

    def scalar_info(self, device, parameter, value_type):
        value = value_type()
        check(self.clGetDeviceInfo(device, parameter, ct.sizeof(value), ct.byref(value), None),
              "query device scalar")
        return value.value

    def discover(self, report):
        count = ct.c_uint32()
        status = self.clGetPlatformIDs(0, None, ct.byref(count))
        if status == CL_PLATFORM_NOT_FOUND_KHR or not count.value and status == CL_SUCCESS:
            return []
        check(status, "clGetPlatformIDs")
        if count.value > 64:
            raise OpenClError("Unexpected platform count exceeds probe limit")
        ids = (ct.c_void_p * count.value)()
        check(self.clGetPlatformIDs(count.value, ids, None), "clGetPlatformIDs")
        devices = []
        for platform_index, handle in enumerate(ids):
            info = {"index": platform_index}
            for field, key in (("name", 0x0902), ("vendor", 0x0903), ("version", 0x0901)):
                info[field] = self.text_info(self.clGetPlatformInfo, handle, key)
            report["platforms"].append(info)
            device_count = ct.c_uint32()
            status = self.clGetDeviceIDs(handle, CL_DEVICE_TYPE_GPU, 0, None, ct.byref(device_count))
            if status == CL_DEVICE_NOT_FOUND or not device_count.value and status == CL_SUCCESS:
                continue
            check(status, "clGetDeviceIDs(GPU)")
            if device_count.value > 64 or len(devices) + device_count.value > 128:
                raise OpenClError("Unexpected GPU count exceeds probe limit")
            handles = (ct.c_void_p * device_count.value)()
            check(self.clGetDeviceIDs(handle, CL_DEVICE_TYPE_GPU, device_count.value, handles, None),
                  "clGetDeviceIDs(GPU)")
            for device in handles:
                item = {"index": len(devices), "platform_index": platform_index,
                        "pci_device_id": None, "pci_bdf": None}
                for field, key in (("name", 0x102B), ("vendor", 0x102C),
                                   ("driver_version", 0x102D), ("device_version", 0x102F),
                                   ("opencl_c_version", 0x103D)):
                    item[field] = self.text_info(self.clGetDeviceInfo, device, key)
                item["reported_type_bits"] = self.scalar_info(device, 0x1000, ct.c_uint64)
                item["reported_vendor_id"] = self.scalar_info(device, 0x1001, ct.c_uint32)
                item["available"] = bool(self.scalar_info(device, 0x1027, ct.c_uint32))
                item["compiler_available"] = bool(self.scalar_info(device, 0x1028, ct.c_uint32))
                item["reported_gpu_without_cpu_type"] = bool(
                    item["reported_type_bits"] & CL_DEVICE_TYPE_GPU and
                    not item["reported_type_bits"] & CL_DEVICE_TYPE_CPU)
                report["devices"].append(item)
                devices.append(device)
        return devices

    def build_log(self, program, device):
        size = ct.c_size_t()
        check(self.clGetProgramBuildInfo(program, device, 0x1183, 0, None, ct.byref(size)), "build log size")
        if size.value > 1024 * 1024:
            raise OpenClError("Build log exceeds probe limit")
        value = ct.create_string_buffer(max(size.value, 1))
        check(self.clGetProgramBuildInfo(program, device, 0x1183, len(value), value, None), "build log")
        return value.value.decode("utf-8", errors="replace")

    def compute(self, device, evidence):
        resources = []
        queue = None

        def created(handle, status, release, label):
            check(status.value, label)
            if not handle:
                raise OpenClError(f"{label}: null handle on successful call")
            resources.append((release, handle))
            return handle

        status = ct.c_int32()
        device_list = (ct.c_void_p * 1)(device)
        try:
            context = created(self.clCreateContext(None, 1, device_list, None, None, ct.byref(status)),
                              status, self.clReleaseContext, "clCreateContext")
            queue = created(self.clCreateCommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE, ct.byref(status)),
                            status, self.clReleaseCommandQueue, "clCreateCommandQueue")
            sources = (ct.c_char_p * 1)(KERNEL)
            lengths = (ct.c_size_t * 1)(len(KERNEL))
            program = created(self.clCreateProgramWithSource(context, 1, sources, lengths, ct.byref(status)),
                              status, self.clReleaseProgram, "clCreateProgramWithSource")
            build_status = self.clBuildProgram(program, 1, device_list, b"-cl-std=CL1.2", None, None)
            evidence["build_log"] = self.build_log(program, device)
            check(build_status, "clBuildProgram")
            kernel = created(self.clCreateKernel(program, b"mellow_substrate", ct.byref(status)),
                             status, self.clReleaseKernel, "clCreateKernel")
            for repetition in range(REPETITIONS):
                nonce = secrets.randbits(32)
                inputs = [(nonce ^ (i * 0x9E3779B9)) & 0xFFFF for i in range(ELEMENTS)]
                expected = [value * 7 + 3 for value in inputs]
                values = (ct.c_uint32 * ELEMENTS)(*inputs)
                buffer = created(self.clCreateBuffer(context, CL_MEM_READ_WRITE | CL_MEM_COPY_HOST_PTR,
                                                    ct.sizeof(values), values, ct.byref(status)),
                                 status, self.clReleaseMemObject, "clCreateBuffer")
                buffer_arg = ct.c_void_p(buffer)
                check(self.clSetKernelArg(kernel, 0, ct.sizeof(buffer_arg), ct.byref(buffer_arg)), "clSetKernelArg")
                global_size = (ct.c_size_t * 1)(ELEMENTS)
                event = ct.c_void_p()
                check(self.clEnqueueNDRangeKernel(queue, kernel, 1, None, global_size, None, 0, None, ct.byref(event)),
                      "clEnqueueNDRangeKernel")
                evidence["submission_occurred"] = True
                if not event.value:
                    raise OpenClError("Kernel enqueue did not return requested event")
                resources.append((self.clReleaseEvent, event.value))
                check(self.clWaitForEvents(1, ct.byref(event)), "clWaitForEvents")
                check(self.clEnqueueReadBuffer(queue, buffer, 1, 0, ct.sizeof(values), values, 0, None, None),
                      "clEnqueueReadBuffer")
                start, end = ct.c_uint64(), ct.c_uint64()
                start_status = self.clGetEventProfilingInfo(event, 0x1282, ct.sizeof(start), ct.byref(start), None)
                end_status = self.clGetEventProfilingInfo(event, 0x1283, ct.sizeof(end), ct.byref(end), None)
                actual = list(values)
                matched = actual == expected
                profiling = start_status == CL_SUCCESS and end_status == CL_SUCCESS and 0 < start.value < end.value
                row = {"repetition": repetition, "nonce": nonce, "elements": ELEMENTS,
                       "input_sha256": hashlib.sha256(struct.pack(f"<{ELEMENTS}I", *inputs)).hexdigest(),
                       "expected_sha256": hashlib.sha256(struct.pack(f"<{ELEMENTS}I", *expected)).hexdigest(),
                       "readback_sha256": hashlib.sha256(struct.pack(f"<{ELEMENTS}I", *actual)).hexdigest(),
                       "expected_sample": expected[:4], "readback_sample": actual[:4],
                       "readback_matches": matched, "gpu_start_ns": start.value, "gpu_end_ns": end.value,
                       "profiling_status": {"start": start_status, "end": end_status},
                       "ordered_nonzero_gpu_timestamps": profiling}
                evidence["runs"].append(row)
                if not matched:
                    raise OpenClError("GPU readback differs from independently computed reference")
            evidence["readback_verified"] = all(row["readback_matches"] for row in evidence["runs"])
            evidence["profiling_verified"] = all(row["ordered_nonzero_gpu_timestamps"] for row in evidence["runs"])
        finally:
            # Drain before releasing buffers/events. If a driver hangs, the
            # parent process deadline terminates this isolated worker.
            cleanup_errors = []
            if queue:
                drain_status = self.clFinish(queue)
                if drain_status != CL_SUCCESS:
                    cleanup_errors.append(f"clFinish: OpenCL status {drain_status}")
            for release, handle in reversed(resources):
                release_status = release(handle)
                if release_status != CL_SUCCESS:
                    cleanup_errors.append(f"{release.__name__}: OpenCL status {release_status}")
            evidence["cleanup_errors"] = cleanup_errors
            if cleanup_errors and sys.exc_info()[0] is None:
                raise OpenClError("; ".join(cleanup_errors))


def probe(compute, device_index):
    report = base_report(compute)
    try:
        runtime = OpenCL()
    except (OSError, AttributeError) as error:
        report["reason"] = f"OpenCL runtime unavailable: {error}"
        return report
    report["runtime_library"] = runtime.path
    try:
        devices = runtime.discover(report)
        if not devices:
            report["reason"] = "No OpenCL GPU device enumerated; CPU fallback is disabled."
            return report
        report["status"] = "GPU_ENUMERATED_ONLY"
        if not compute:
            return report
        if device_index >= len(devices):
            report["status"] = "INVALID_DEVICE_SELECTION"
            return report
        selected = report["devices"][device_index]
        report["selected_device_index"] = device_index
        if not all(selected[key] for key in ("available", "compiler_available", "reported_gpu_without_cpu_type")):
            report["status"] = "NOT_AVAILABLE"
            report["reason"] = "Selected device is unavailable, has no compiler, or is not exclusively GPU classified."
            return report
        evidence = {"kernel_source": KERNEL.decode("ascii"),
                    "kernel_sha256": hashlib.sha256(KERNEL).hexdigest(),
                    "build_options": "-cl-std=CL1.2", "build_log": None,
                    "submission_occurred": False, "readback_verified": False,
                    "profiling_verified": False, "runs": []}
        report["compute"] = evidence
        runtime.compute(devices[device_index], evidence)
        report["opencl_gpu_compute_pass"] = evidence["readback_verified"] and evidence["profiling_verified"]
        report["macos_driver_tested"] = platform.system() == "Darwin"
        report["status"] = ("PASS_OPENCL_GPU_SUBSTRATE_ONLY" if report["opencl_gpu_compute_pass"]
                            else "EXECUTED_INCOMPLETE_EVIDENCE")
    except (OpenClError, OSError, ValueError) as error:
        report["status"] = "FAILED"
        report["error"] = str(error)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compute", action="store_true", help="Execute only the fixed 256-element kernel three times")
    parser.add_argument("--device-index", type=int, default=0, help="GPU-only enumeration index; no CPU fallback")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--timeout", type=int, default=30, help="Worker deadline in seconds (1-120)")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.device_index < 0 or not 1 <= args.timeout <= 120:
        parser.error("device index must be nonnegative and timeout must be 1-120 seconds")
    if args.worker:
        report = probe(args.compute, args.device_index)
    else:
        with tempfile.TemporaryDirectory(prefix="mellow-opencl-probe-") as temp:
            result_path = Path(temp) / "result.json"
            command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--report", str(result_path),
                       "--device-index", str(args.device_index)]
            if args.compute:
                command.append("--compute")
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            try:
                worker = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout, **options)
                if result_path.exists():
                    report = json.loads(result_path.read_text(encoding="utf-8"))
                    report["worker_exit_code"] = worker.returncode
                    if worker.returncode and report["status"] in ("GPU_ENUMERATED_ONLY", "PASS_OPENCL_GPU_SUBSTRATE_ONLY"):
                        report["status"] = "WORKER_FAILED"
                        report["opencl_gpu_compute_pass"] = False
                else:
                    report = base_report(args.compute)
                    report.update(status="WORKER_FAILED", worker_exit_code=worker.returncode,
                                  worker_stderr=worker.stderr[-4096:])
            except subprocess.TimeoutExpired:
                report = base_report(args.compute)
                report.update(status="TIMED_OUT", reason="Isolated OpenCL worker exceeded deadline and was terminated.")
                report["execution_after_timeout"] = "unknown; no successful GPU claim is made"
            except (OSError, ValueError) as error:
                report = base_report(args.compute)
                report.update(status="WORKER_FAILED", error=str(error))
            report["worker_deadline_seconds"] = args.timeout
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not args.worker:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] in ("GPU_ENUMERATED_ONLY", "PASS_OPENCL_GPU_SUBSTRATE_ONLY") else 2


if __name__ == "__main__":
    raise SystemExit(main())
