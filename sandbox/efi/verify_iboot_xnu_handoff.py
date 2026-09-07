#!/usr/bin/env python3
"""Verify a saved VMApple iBoot -> XNU evidence report.

This verifier is intentionally offline: it reads one JSON report and never
starts QEMU, opens firmware, uploads USB data, or modifies a guest input.
Exit status 0 means the report is internally consistent; a consistent report
may still be blocked before XNU.  Exit status 2 means malformed scope or an
impossible positive claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Executing this file directly (the documented form) puts sandbox/efi on
# sys.path rather than the repository root.  Add the root explicitly without
# relying on the caller's PYTHONPATH.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from x86.iboot_handoff import HandoffContractError, verify_handoff_report


def verify_file(path: Path, *, expected_target_major: int | None = None,
                require_recovery_chain: bool = False) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HandoffContractError(f"cannot read JSON report {path}: {exc}") from exc
    return verify_handoff_report(
        payload,
        expected_target_major=expected_target_major,
        require_recovery_chain=require_recovery_chain,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--target-major", type=int, choices=(26, 27))
    parser.add_argument("--require-recovery-chain", action="store_true")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        result = verify_file(
            args.report,
            expected_target_major=args.target_major,
            require_recovery_chain=args.require_recovery_chain,
        )
    except HandoffContractError as exc:
        result = {"schema": "26x86.iboot-xnu-handoff/1", "valid": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False,
                         separators=(",", ":") if args.compact else None, indent=None if args.compact else 2))
        return 2
    print(json.dumps(result, ensure_ascii=False,
                     separators=(",", ":") if args.compact else None, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
