"""Bounded AIR/metallib input decoding. This module does not execute GPU work.

The bitcode wrapper follows LLVM's documented format. Metallib layout is based
on YuAo/MetalLibraryArchive, commit de573ba4a7b986bbecb3e4ce2464945d266a28e9,
README's Binary Layout and Archive.swift, and checked against real SDL artifacts.
Only executable metallib format 2.2/2.4 and self-contained MDSZ entries are read.
No private Apple compiler or kernel ABI is inferred by this container reader.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import time

MAX_INPUT = 4 * 1024 * 1024
MAX_IR = 8 * 1024 * 1024
MAX_LOG = 256 * 1024
MAGIC = b"BC\xc0\xde"
WRAPPER = b"\xde\xc0\x17\x0b"


class AirError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounded_read(path: Path, limit: int = MAX_INPUT) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise AirError("input exceeds byte limit")
    return data


def span(data: bytes, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise AirError("section extends beyond input")
    return bytes(data[offset:offset + size])


def unpack_bitcode(data: bytes) -> tuple[bytes, dict]:
    if not 4 <= len(data) <= MAX_INPUT:
        raise AirError("invalid bitcode size")
    if data.startswith(MAGIC):
        return data, {"container": "raw-bitcode", "bitcode_sha256": sha256(data)}
    if not data.startswith(WRAPPER):
        raise AirError("not LLVM raw or wrapped bitcode")
    if len(data) < 20:
        raise AirError("truncated LLVM wrapper")
    _, version, offset, size, cpu = struct.unpack_from("<5I", data)
    if version != 0 or offset < 20 or not size:
        raise AirError("unsupported LLVM wrapper version/offset/size")
    bitcode = span(data, offset, size)
    if not bitcode.startswith(MAGIC):
        raise AirError("LLVM wrapper payload has no bitcode magic")
    # LLVM writers pad wrappers to a 16-byte boundary. No hidden second payload.
    suffix = data[offset + size:]
    if len(suffix) > 15 or any(suffix):
        raise AirError("non-padding trailing wrapper payload")
    return bitcode, {"container": "wrapped-bitcode", "wrapper_version": version,
                     "wrapper_cpu_type": cpu, "payload_offset": offset,
                     "bitcode_sha256": sha256(bitcode)}


def _tags(data: bytes) -> dict[bytes, bytes]:
    result = {}
    offset = 0
    while True:
        tag = span(data, offset, 4)
        offset += 4
        if tag == b"ENDT":
            if offset != len(data):
                raise AirError("trailing bytes in tag group")
            return result
        if tag in result:
            raise AirError("duplicate metallib tag")
        length, = struct.unpack("<H", span(data, offset, 2))
        offset += 2
        result[tag] = span(data, offset, length)
        offset += length


def unpack_metallib(data: bytes) -> list[dict]:
    if not 88 <= len(data) <= MAX_INPUT or data[:4] != b"MTLB":
        raise AirError("not a bounded metallib")
    platform, major, minor = struct.unpack_from("<3H", data, 4)
    if platform not in (1, 0x8001) or (major, minor) not in ((2, 2), (2, 4)):
        raise AirError("unsupported metallib platform/version")
    if data[10] != 0:
        raise AirError("only executable metallib input is supported")
    total, = struct.unpack_from("<Q", data, 16)
    if total != len(data):
        raise AirError("metallib declared size mismatch")
    fo, fs, po, ps, ro, rs, bo, bs = struct.unpack_from("<8Q", data, 24)
    # The function-list size ends at the start of its final ENDT, excluding four
    # bytes. Each group's length includes its length word and terminal ENDT.
    intervals = [(fo, fs + 4), (po, ps), (ro, rs), (bo, bs)]
    previous = 88
    for index, (start, length) in enumerate(intervals):
        if start < previous or not length:
            raise AirError("overlapping, unordered or empty metallib sections")
        if index >= 2 and start != previous:
            raise AirError("unsupported gap between metallib sections")
        span(data, start, length)
        previous = start + length
    if previous != len(data) or fo != 88:
        raise AirError("unsupported metallib gaps/header extension")
    if span(data, fo + fs, 4) != b"ENDT":
        raise AirError("missing function-list end marker")
    gap = span(data, fo + fs + 4, po - (fo + fs + 4))
    if gap not in (b"", b"ENDT"):
        raise AirError("unsupported metallib header extension")
    count, = struct.unpack("<I", span(data, fo, 4))
    if not 1 <= count <= 1024:
        raise AirError("invalid function count")
    cursor = fo + 4
    result = []
    names = set()
    ranges = []
    for _ in range(count):
        length, = struct.unpack("<I", span(data, cursor, 4))
        if length < 8 or cursor + length > fo + fs + 4:
            raise AirError("function group exceeds section")
        tags = _tags(span(data, cursor + 4, length - 4))
        cursor += length
        required = {b"NAME", b"TYPE", b"HASH", b"MDSZ", b"OFFT", b"VERS"}
        if set(tags) != required:
            raise AirError("unsupported or missing function tags")
        name_bytes = tags[b"NAME"]
        if len(name_bytes) < 2 or name_bytes[-1:] != b"\0" or b"\0" in name_bytes[:-1]:
            raise AirError("invalid function name")
        try:
            name = name_bytes[:-1].decode("utf-8")
        except UnicodeError as exc:
            raise AirError("invalid function name encoding") from exc
        if len(name) > 1024 or name in names:
            raise AirError("duplicate or overlong function name")
        names.add(name)
        for key, length in ((b"TYPE", 1), (b"HASH", 32), (b"MDSZ", 8), (b"OFFT", 24), (b"VERS", 8)):
            if len(tags[key]) != length:
                raise AirError("invalid fixed-size function tag")
        kind = tags[b"TYPE"][0]
        if kind > 6:
            raise AirError("unknown function kind")
        bit_size, = struct.unpack("<Q", tags[b"MDSZ"])
        pub, private, bit = struct.unpack("<3Q", tags[b"OFFT"])
        if not bit_size or bit > bs or bit_size > bs - bit:
            raise AirError("function bitcode exceeds section")
        for begin, end in ranges:
            if bit < end and begin < bit + bit_size:
                raise AirError("overlapping function bitcode")
        ranges.append((bit, bit + bit_size))
        # Parse selected public/private metadata strictly, without treating tags
        # as Metal execution capabilities. AIR semantic lowering is separate.
        metadata = []
        for base, size, relative in ((po, ps, pub), (ro, rs, private)):
            if relative > size or size - relative < 8:
                raise AirError("function metadata offset outside section")
            tag_size, = struct.unpack("<I", span(data, base + relative, 4))
            if tag_size < 4 or tag_size > size - relative - 4:
                raise AirError("function metadata length outside section")
            metadata.append(_tags(span(data, base + relative + 4, tag_size)))
        payload = span(data, bo + bit, bit_size)
        if hashlib.sha256(payload).digest() != tags[b"HASH"]:
            raise AirError("function bitcode HASH mismatch")
        raw, wrapper = unpack_bitcode(payload)
        result.append({"name": name, "kind": kind, "air_msl_versions": list(struct.unpack("<4H", tags[b"VERS"])),
                       "payload_sha256": sha256(payload), "bitcode": raw,
                       "wrapper": wrapper, "metadata_tags": [[k.decode("ascii", errors="replace") for k in m] for m in metadata]})
    if cursor != fo + fs + 4:
        raise AirError("function count/length mismatch")
    return result


def decode_input(data: bytes, entry: str | None = None) -> tuple[bytes, dict]:
    if data.startswith(b"MTLB"):
        functions = unpack_metallib(data)
        if entry is None:
            if len(functions) != 1:
                raise AirError("entry required for multi-function metallib")
            selected = functions[0]
        else:
            matches = [f for f in functions if f["name"] == entry]
            if len(matches) != 1:
                raise AirError("entry not present in metallib")
            selected = matches[0]
        metadata = {k: v for k, v in selected.items() if k != "bitcode"}
        metadata.update(container="metallib", function_count=len(functions), input_sha256=sha256(data))
        return selected["bitcode"], metadata
    raw, info = unpack_bitcode(data)
    info["input_sha256"] = sha256(data)
    return raw, info


def disassemble(data: bytes, llvm_dis: Path, *, entry: str | None = None,
                timeout: float = 15.0) -> tuple[str, dict]:
    """Decode with an explicitly supplied real llvm-dis, in an isolated directory.

    Deadline and file-size supervision bound ordinary failed tool output. This is
    not a security sandbox for a malicious compiler executable or LLVM parser.
    No shell, fallback parser, stale output or source text is accepted as success.
    """
    if not 0 < timeout <= 60:
        raise AirError("invalid compiler timeout")
    executable = llvm_dis.resolve(strict=True)
    before = sha256(executable.read_bytes())
    raw, metadata = decode_input(data, entry)
    with tempfile.TemporaryDirectory(prefix="mellow-air-") as directory:
        base = Path(directory)
        source, output, diagnostic = base / "input.bc", base / "decoded.ll", base / "diagnostic.txt"
        source.write_bytes(raw)
        with diagnostic.open("wb") as log:
            try:
                process = subprocess.Popen([str(executable), str(source), "-o", str(output)],
                                           cwd=base, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
            except OSError as exc:
                raise AirError("cannot start llvm-dis: " + str(exc)) from exc
            deadline = time.monotonic() + timeout
            failure = None
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    failure = "llvm-dis timed out"
                elif diagnostic.stat().st_size > MAX_LOG or (output.exists() and output.stat().st_size > MAX_IR):
                    failure = "llvm-dis output exceeds byte limit"
                if failure:
                    process.kill()
                    process.wait(timeout=5)
                    break
                time.sleep(0.01)
            if failure:
                raise AirError(failure)
        error_log = bounded_read(diagnostic, MAX_LOG).decode("utf-8", errors="replace")
        if process.returncode != 0 or not output.is_file():
            raise AirError("llvm-dis failed: " + error_log[:2000])
        try:
            ir = bounded_read(output, MAX_IR).decode("utf-8")
        except UnicodeError as exc:
            raise AirError("invalid UTF-8 LLVM assembly") from exc
        if sha256(executable.read_bytes()) != before or source.read_bytes() != raw:
            raise AirError("compiler or bitcode changed during decoding")
    if not ir.strip():
        raise AirError("llvm-dis emitted empty assembly")
    metadata.update(llvm_dis=str(executable), llvm_dis_sha256=before, llvm_ir_sha256=sha256(ir.encode()),
                    decoded_by_llvm=True, shader_lowered=False, gpu_executed=False,
                    apple_compiler_origin_authenticated=False)
    return ir, metadata


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--entry")
    parser.add_argument("--llvm-dis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.report.resolve():
        parser.error("output and report must be different paths")
    # Refuse clobbering. Failed invocations must not leave a previous PASS output.
    if args.output.exists() or args.report.exists():
        parser.error("output and report must be new paths")
    report = {"schema_version": 1, "status": "FAIL", "gpu_executed": False, "shader_lowered": False}
    try:
        ir, metadata = disassemble(bounded_read(args.input), args.llvm_dis, entry=args.entry)
        report.update(metadata)
        args.output.write_text(ir, encoding="utf-8", newline="\n")
        report["status"] = "DECODED_LLVM_IR_ONLY"
    except (AirError, OSError) as exc:
        report["error"] = str(exc)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "gpu_executed", "shader_lowered")}))
    return 0 if report["status"] == "DECODED_LLVM_IR_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
