#!/usr/bin/env python3
"""Inspect Linux GPU source, plan an XNU port, and generate bounded review artifacts."""
import argparse
import json
from pathlib import Path
import sys

from mellow_port import PortError, prepare


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inspect", "plan", "generate"))
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=("xe", "amdgpu", "nvidia-open"))
    parser.add_argument("--revision", required=True, help="Full 40/64 hex immutable source revision claim; actual file SHA256 is measured")
    parser.add_argument("--source-url", help="Optional upstream provenance URL claim")
    parser.add_argument("--file", action="append", required=True, dest="files", help="Explicit source-relative POSIX allowlist path; repeat as needed")
    parser.add_argument("--output", required=True, type=Path, help="New/empty directory outside the source tree")
    parser.add_argument("--require-ready", action="store_true", help="Exit 2 after emitting gaps because functional driver readiness is not implemented")
    args = parser.parse_args(argv)
    try:
        result = prepare(args.operation, args.source_root, args.target, args.revision, args.files, args.output, args.source_url, args.require_ready)
    except (PortError, OSError) as error:
        print(json.dumps({"artifacts_generated": False, "driver_ready": False, "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
