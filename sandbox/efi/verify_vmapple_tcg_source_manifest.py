#!/usr/bin/env python3
"""Validate the source/provenance manifest for the portable VMApple layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "vmapple-tcg-source-port-manifest.json"
REQUIRED_CONTRACT_FIELDS = {
    "reset_behavior", "mmio_pio_map", "register_layout", "read_behavior",
    "write_side_effects", "irq_behavior", "dma_behavior", "timer_behavior",
    "firmware_visible_identity", "device_tree_acpi_exposure", "boot_time_dependency",
}
REQUIRED_EVIDENCE_FIELDS = {
    "references", "source_trace", "guest_driver_trace", "register_differential_test",
    "venfire_test_evidence", "evidence_status",
}
VALID_STATES = {"planned", "in-progress", "runtime-tested", "blocked"}
VALID_MODES = {"direct-port", "adapted-port", "clean-room-reimplementation", "behavior-reference-only"}


def validate(path: Path = MANIFEST) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1:
        raise ValueError("unsupported VMApple TCG source manifest schema")
    if document.get("target_machine_profile") != "VMApple-TCG-GoldenGate":
        raise ValueError("source manifest must target VMApple-TCG-GoldenGate")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("source manifest has no components")
    names: set[str] = set()
    state_counts: dict[str, int] = {}
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("source manifest component must be an object")
        name = component.get("name")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"duplicate or invalid component name: {name!r}")
        names.add(name)
        if component.get("target_machine_profile") != document["target_machine_profile"]:
            raise ValueError(f"profile mismatch for {name}")
        source = component.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"missing source for {name}")
        for field in ("project", "upstream_repository", "upstream_commit", "upstream_file_path", "source_license", "provenance_status"):
            if not isinstance(source.get(field), str) or not source[field]:
                raise ValueError(f"missing source.{field} for {name}")
        port = component.get("port")
        if not isinstance(port, dict) or port.get("mode") not in VALID_MODES:
            raise ValueError(f"invalid port mode for {name}")
        contract = component.get("guest_contract")
        if not isinstance(contract, dict) or not REQUIRED_CONTRACT_FIELDS <= set(contract):
            raise ValueError(f"incomplete guest contract for {name}")
        evidence = component.get("evidence")
        if not isinstance(evidence, dict) or not REQUIRED_EVIDENCE_FIELDS <= set(evidence):
            raise ValueError(f"incomplete evidence for {name}")
        if not isinstance(evidence["references"], list) or len(evidence["references"]) < 2:
            raise ValueError(f"component needs two reference perspectives: {name}")
        state = component.get("state")
        if state not in VALID_STATES:
            raise ValueError(f"invalid state for {name}")
        state_counts[state] = state_counts.get(state, 0) + 1
        if not isinstance(component.get("known_gaps"), str) or not component["known_gaps"]:
            raise ValueError(f"known_gaps is required for {name}")
    return {
        "schema_version": 1,
        "target_machine_profile": document["target_machine_profile"],
        "component_count": len(components),
        "component_states": state_counts,
        "valid": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        result = validate(args.manifest.resolve(strict=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, separators=(",", ":") if args.compact else None))
        return 2
    print(json.dumps(result, separators=(",", ":") if args.compact else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
