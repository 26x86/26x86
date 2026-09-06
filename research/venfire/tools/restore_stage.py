#!/usr/bin/env python3
"""Prepare official restore-role containers and continue an existing Apple chain.

All generated containers and private TSS responses go under the new output
directory. Original inputs are read-only. Boot success requires actual guest
logs; a completed transfer sequence does not establish XNU/macOS execution.
Boot requires the same live VM's verified iBEC/LocalPolicy personalization
directory. Independent batch TSS requests are available for diagnostics only.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venfire.artifacts import create_manifest, require_intact, verify_manifest
from venfire.policy import authorize_host
from venfire.restore import ROLE_TAGS, prepare_role_container, wrap_role_container, run_stage


def execute(args):
    authorization = authorize_host(developer_host_bypass=args.developer_host_bypass)
    chain = getattr(args, "chain_personalization", None)
    if args.boot and not chain:
        raise ValueError("Boot requires --chain-personalization for the same live VM's accepted iBEC/LocalPolicy chain; a fresh batch ticket is not that chain")
    if not chain and not args.helper:
        raise ValueError("Independent batch TSS requests require --helper")
    from venfire.personalization import read_build_manifest, request_restore_ticket
    components = {}
    for spec in args.component:
        role, separator, filename = spec.partition("=")
        if not separator or role not in ROLE_TAGS or role in components:
            raise ValueError("Expected one unique supported Role=/absolute/file entry")
        components[role] = Path(filename).absolute()
    if args.boot and not {"RestoreTrustCache", "RestoreRamDisk", "RestoreDeviceTree", "RestoreKernelCache"} <= components.keys():
        raise ValueError("Boot requires trust cache, ramdisk, Device Tree and kernel components")
    originals = create_manifest([args.manifest, *components.values(), *([args.helper] if args.helper else [])])
    manifest = read_build_manifest(args.manifest)
    identities = [identity for identity in manifest["BuildIdentities"]
                  if identity["Info"].get("DeviceClass") == "vma2macosap"
                  and identity["Info"].get("Variant") == "Customer Erase Install (IPSW)"]
    if len(identities) != 1:
        raise ValueError("Expected a unique official VMApple erase restore identity")
    directory = args.output.absolute()
    directory.mkdir(parents=True, exist_ok=False)
    directory.chmod(0o700)
    prepared_dir, wrapped_dir = directory / "prepared", directory / "personalized"
    prepared_dir.mkdir()
    wrapped_dir.mkdir()
    report = {"schema": 1, "host_authorization": authorization.to_dict(),
              "prepared": {}, "personalized": {}, "error": None,
              "ticket_mode": "existing-ibec-localpolicy-chain" if chain else "independent-batch-diagnostic",
              "macos_boot_verified": False, "xnu_boot_verified": False}
    interruption = None
    try:
        require_intact(originals)
        prepared = {}
        for role, source in components.items():
            target = prepared_dir / (role + ".im4p")
            report["prepared"][role] = prepare_role_container(source, role,
                identities[0]["Manifest"][role]["Digest"], target)
            prepared[role] = str(target)
        if chain:
            from venfire.personalization import reuse_restore_ticket
            report["tss"] = reuse_restore_ticket(socket_path=args.socket,
                build_manifest=args.manifest, components=prepared,
                chain_personalization=chain, output=directory / "tss",
                developer_host_bypass=args.developer_host_bypass,
                original_inputs=list(components.values()))
        else:
            report["tss"] = request_restore_ticket(socket_path=args.socket,
                build_manifest=args.manifest, components=prepared, helper=args.helper,
                output=directory / "tss", developer_host_bypass=args.developer_host_bypass,
                original_inputs=list(components.values()))
        if not report["tss"].get("ticket_received"):
            raise ValueError("Apple did not issue a restore ticket")
        ticket = report["tss"]["ticket_path"]
        images = {}
        for role, source in prepared.items():
            target = wrapped_dir / (role + ".img4")
            proof = wrap_role_container(source, ticket, target)
            report["personalized"][role] = proof
            images[role] = {"path": str(target), "sha256": proof["sha256"]}
        if args.boot:
            report["restore"] = run_stage(args.socket, images, total_timeout=args.total_timeout)
    except BaseException as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        if hasattr(exc, "restore_report"):
            report["restore"] = exc.restore_report
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            interruption = exc
    finally:
        report["input_integrity"] = verify_manifest(originals).to_dict()
        (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if interruption is not None:
        raise interruption
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--component", action="append", required=True, metavar="ROLE=FILE")
    parser.add_argument("--helper", type=Path,
        help="TSS request encoder for independent batch diagnostics; unnecessary when reusing a verified existing chain")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--developer-host-bypass", action="store_true")
    parser.add_argument("--boot", action="store_true")
    parser.add_argument("--chain-personalization", type=Path,
        help="Existing iBEC personalization directory whose Apple ticket is bound by this live VM's accepted restore LocalPolicy")
    parser.add_argument("--total-timeout", type=float, default=600)
    args = parser.parse_args()
    try:
        report = execute(args)
        print(json.dumps(report, indent=2))
        return 1 if report["error"] or report.get("restore", {}).get("error") or not report["input_integrity"]["valid"] else 0
    except Exception as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
