#!/usr/bin/env python3
"""Adversarial validation tests based on a real built driver, never a substitute driver."""
import importlib.util
import struct
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", root / "Tools/validate-macho.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_macho_validation.py path/to/actual/Mellow.kext/Contents/MacOS/Mellow")
    original = Path(sys.argv[1]).read_bytes()
    passed = 0
    with tempfile.TemporaryDirectory(prefix="mellow-validator-") as temporary:
        path = Path(temporary) / "mutation-only-for-validation"
        path.write_bytes(original)
        assert validator.inspect_binary(path)["structural_validation_passed"]
        passed += 1
        for kind in (1, 2, 6, 8):
            data = bytearray(original)
            struct.pack_into("<I", data, 12, kind)
            path.write_bytes(data)
            assert not validator.inspect_binary(path)["structural_validation_passed"], kind
            passed += 1
        for data in (original[:8], original[:32], original[:-128]):
            path.write_bytes(data)
            try:
                result = validator.inspect_binary(path)
                assert not result["structural_validation_passed"]
            except ValueError:
                pass
            passed += 1
        data = bytearray(original)
        struct.pack_into("<I", data, 36, 0)
        path.write_bytes(data)
        try:
            validator.inspect_binary(path)
            raise AssertionError("Accepted zero-sized load command")
        except ValueError:
            passed += 1
        data = bytearray(original)
        struct.pack_into("<I", data, 4, 0x0100000C)
        path.write_bytes(data)
        try:
            validator.inspect_binary(path)
            raise AssertionError("Accepted ARM64 instead of x86_64")
        except ValueError:
            passed += 1
    print(f"PASS: {passed} real-artifact structural/rejection tests")


if __name__ == "__main__":
    main()
