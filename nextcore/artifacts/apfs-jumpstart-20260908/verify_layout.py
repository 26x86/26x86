#!/usr/bin/env python3
"""Compile the authored C layout model and validate public APFS offsets/vectors."""
import argparse
import hashlib
import json
import pathlib
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=pathlib.Path, required=True)
    parser.add_argument("--cc", default="gcc")
    args = parser.parse_args()
    here = pathlib.Path(__file__).resolve().parent
    args.work_dir.mkdir(parents=True, exist_ok=True)
    executable = args.work_dir / "layout_fixture"
    command = [args.cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
               str(here / "layout_fixture.c"), "-o", str(executable)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if compiled.returncode:
        raise RuntimeError(compiled.stdout + compiled.stderr)
    executed = subprocess.run([str(executable)], capture_output=True, text=True,
                              check=True, timeout=5)
    output = json.loads(executed.stdout)
    assert output["sizes"] == {"obj_phys": 32, "prange": 16,
                               "nx_superblock": 1408, "nx_efi_jumpstart": 176}
    assert output["offsets"] == {
        "o_oid": 8, "o_xid": 16, "o_type": 24, "o_subtype": 28,
        "nx_magic": 32, "nx_block_size": 36, "nx_block_count": 40,
        "nx_features": 48, "nx_readonly_compatible_features": 56,
        "nx_incompatible_features": 64, "nx_uuid": 72, "nx_flags": 1264,
        "nx_efi_jumpstart": 1272, "nx_fusion_uuid": 1280,
        "nx_fusion_mt_oid": 1352, "nx_fusion_wbc_oid": 1360,
        "nx_fusion_wbc": 1368, "nej_magic": 32, "nej_version": 36,
        "nej_efi_file_len": 40, "nej_num_extents": 44,
        "nej_reserved": 48, "nej_rec_extents": 176, "pr_block_count": 8,
    }
    assert output["checksums"] == [
        {"size": 4096, "pattern": 0, "checksum": "ffffffffffffffff", "residue": [0, 0]},
        {"size": 4096, "pattern": 1, "checksum": "ba20c0635340cfba", "residue": [0, 0]},
        {"size": 65536, "pattern": 1, "checksum": "111d325c075e55c2", "residue": [0, 0]},
        {"size": 4096, "pattern": 2, "checksum": "ffffffffffffffff", "residue": [0, 0]},
    ]
    receipt = {
        "passed": True,
        "layer": "authored C public layout and mathematical checksum cross-check",
        "command": command,
        "compiler": subprocess.check_output([args.cc, "--version"], text=True).splitlines()[0],
        "source_sha256": hashlib.sha256((here / "layout_fixture.c").read_bytes()).hexdigest(),
        "output": output,
        "actual_apfs_media_read": False,
        "efi_driver_executed": False,
    }
    (here / "layout-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "offsets": len(output["offsets"]),
                      "checksum_vectors": len(output["checksums"])}))


if __name__ == "__main__":
    main()
