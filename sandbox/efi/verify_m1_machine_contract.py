#!/usr/bin/env python3
"""Validate the M1-only machine graph ledger before any port is claimed.

This verifier deliberately validates the *absence* boundary as well as the
schema.  A blocked entry is a successful result when its missing provenance or
runtime evidence is explicit; a guessed generic platform is a failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT / "m1-machine-contract.json"
REQUIRED = {
    "cpu-topology-and-system-state",
    "memory-map-and-reset",
    "apple-interrupt-controller",
    "timer-and-counter",
    "firmware-identity-and-handoff",
    "serial-and-diagnostic-channel",
    "storage-controller-and-provisioning",
    "dma-and-iommu",
    "recovery-transport",
    "display-path",
    "iboot-xnu-macos-boot-chain",
}
FORBIDDEN_FALLBACKS = {
    "generic-arm-virt",
    "qemu-t8030",
    "gicv3",
    "m2-or-later",
    "iphone-or-ipad",
    "u-boot",
    "windows-arm",
}


def validate(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "venfire-m1-machine-contract/1":
        raise ValueError("unsupported machine-contract schema")
    if document.get("target_machine_profile") != "M1-only":
        raise ValueError("machine contract must be M1-only")
    fallbacks = set(document.get("fallbacks_forbidden", []))
    if fallbacks != FORBIDDEN_FALLBACKS:
        raise ValueError("fallback prohibition set changed")
    components = document.get("components")
    if not isinstance(components, list) or len(components) != len(REQUIRED):
        raise ValueError("component list is incomplete or duplicated")
    seen = set()
    blocked = 0
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("component is not an object")
        name = component.get("name")
        if name not in REQUIRED or name in seen:
            raise ValueError(f"unexpected or duplicate component: {name!r}")
        seen.add(name)
        if component.get("phase") not in (3, 4, 5):
            raise ValueError(f"invalid phase for {name}")
        if component.get("state") not in ("planned", "in-progress", "runtime-tested", "blocked"):
            raise ValueError(f"invalid state for {name}")
        source = component.get("source")
        if not isinstance(source, dict) or not source.get("project"):
            raise ValueError(f"missing source record for {name}")
        if component.get("state") == "runtime-tested":
            if source.get("upstream_commit") in (None, "not recorded"):
                raise ValueError(f"runtime-tested component lacks immutable source: {name}")
        if component.get("state") == "blocked":
            blocked += 1
            if not component.get("known_gap"):
                raise ValueError(f"blocked component lacks known_gap: {name}")
        destination = component.get("venfire_destination", "")
        if any(token in destination.lower() for token in ("qemu-t8030", "generic-arm-virt", "gicv3")):
            raise ValueError(f"forbidden fallback named as Venfire destination: {name}")
    if seen != REQUIRED:
        raise ValueError(f"missing components: {sorted(REQUIRED - seen)}")
    return {
        "schema": document["schema"],
        "target_machine_profile": document["target_machine_profile"],
        "component_count": len(components),
        "blocked_components": blocked,
        "runtime_tested_components": sum(c["state"] == "runtime-tested" for c in components),
        "passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    report = validate(args.contract.resolve(strict=True))
    print(json.dumps(report, sort_keys=True) if args.compact else json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
