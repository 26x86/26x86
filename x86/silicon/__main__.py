"""
CLI for the Apple Silicon sandbox boot/DFU SIMULATION — see x86/silicon/__init__.py.

Usage:
  python -m x86.silicon session [--host ID] [--json]
  python -m x86.silicon hosts [--json]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Optional


def _emit_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _print_session(payload: dict[str, Any]) -> None:
    logging.info("== Apple Silicon sandbox — %s (SIMULATED, not a real boot) ==", payload["target_os_name"])
    logging.info("host: %s", payload["host_label"])
    for stage in payload["boot_chain"]["stages"]:
        logging.info("[%s] %s — %s", stage["status"], stage["title"], stage["purpose"])
    logging.info("blocked at: %s", payload["boot_chain"]["blocked_at"])
    logging.info("-- DFU handshake --")
    for transition in payload["dfu_trace"]["transitions"]:
        logging.info("%s -> %s: %s", transition["from"], transition["to"], transition["event"])
    logging.info("dfu final state: %s (ok=%s)", payload["dfu_trace"]["final_state"], payload["dfu_trace"]["ok"])
    for note in payload["notes"]:
        logging.info("NOTE: %s", note)
    logging.info(
        "simulated=%s real_boot_verified=%s xnu_executed=%s",
        payload["simulated"], payload["real_boot_verified"], payload["xnu_executed"],
    )


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="python -m x86.silicon",
        description="Apple Silicon sandbox boot/DFU simulation (never a real boot; see x86/silicon/__init__.py)",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p_session = sub.add_parser("session", help="Run one simulated install session")
    p_session.add_argument("--host", help="One of the fixture ids from `hosts`")
    p_session.add_argument("--json", action="store_true")

    p_hosts = sub.add_parser("hosts", help="List available fixture hosts")
    p_hosts.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.action == "hosts":
        from x86.silicon.mock_host import HOSTS

        rows = [{"host_id": host.host_id, "label": host.label, "notes": list(host.notes)} for host in HOSTS]
        if args.json:
            _emit_json({"hosts": rows})
        else:
            for row in rows:
                logging.info("%s — %s", row["host_id"], row["label"])
        return 0

    if args.action == "session":
        from x86.silicon.mock_host import HOSTS
        from x86.silicon.session import run_install_session

        kwargs: dict[str, Any] = {}
        if args.host:
            match = next((host for host in HOSTS if host.host_id == args.host), None)
            if match is None:
                logging.error("Unknown host id: %s", args.host)
                return 2
            kwargs = {
                "target_os": match.target_os_kernel,
                "inject_dfu_failure_at": match.inject_dfu_failure_at,
                "host_label": match.label,
            }
        result = run_install_session(**kwargs)
        payload = result.as_dict()
        if args.json:
            _emit_json(payload)
        else:
            _print_session(payload)
        return 0 if result.ok else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
