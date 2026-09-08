#!/usr/bin/env python3
"""Gate one exact prepared/remote commit in an independent Linux-only parent."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import struct
import subprocess
import tempfile
import time
import tomllib

HERE = Path(__file__).resolve().parent


def mounted(path):
    p = PureWindowsPath(path)
    return Path("/mnt") / p.drive[0].lower() / Path(*p.parts[1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("module", choices=["Core", "EFI", "Tool"])
    ap.add_argument("phase", choices=["pre", "post"])
    ap.add_argument("--attempt", type=int, default=1)
    args = ap.parse_args()
    prepared = json.loads((HERE / f"{args.module}-prepared.json").read_text())
    out = HERE / "gates" / args.phase / args.module / f"r{args.attempt}"
    out.mkdir(parents=True, exist_ok=False)
    parent = Path(tempfile.mkdtemp(prefix=f"nextcore-apfs-release-{args.module.lower()}-{args.phase}-"))
    repo = parent / "module"
    env = os.environ.copy()
    env["PATH"] = "/home/developer/.cargo/bin:" + env["PATH"]
    env["CARGO_TERM_COLOR"] = "never"
    env["CARGO_BUILD_JOBS"] = "2"
    result = {"module": args.module, "phase": args.phase, "attempt": args.attempt,
              "source_commit": prepared["source_commit"], "expected_head": prepared["head"],
              "tag": prepared["tag"], "single_repo_parent": str(parent), "commands": [],
              "passed": False, "guest_execution_claimed": False}

    def run(argv, cwd=None, timeout=600):
        start = time.monotonic()
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        index = len(result["commands"])
        (out / f"{index}.stdout").write_bytes(p.stdout)
        (out / f"{index}.stderr").write_bytes(p.stderr)
        result["commands"].append({"argv": argv, "exit_code": p.returncode,
            "elapsed_seconds": round(time.monotonic() - start, 3),
            "stdout": f"{index}.stdout", "stderr": f"{index}.stderr"})
        print(json.dumps({"module": args.module, "phase": args.phase,
                          "command": index, "exit_code": p.returncode}), flush=True)
        if p.returncode:
            raise RuntimeError(p.stderr.decode(errors="replace")[-6000:])
        return p.stdout

    try:
        source = str(mounted(prepared["path"])) if args.phase == "pre" else f"https://github.com/{prepared['repository']}.git"
        clone = ["git", "clone", "--no-local", "--config", "core.autocrlf=false", "--config", "core.eol=lf"]
        if args.phase == "post":
            clone += ["--branch", prepared["tag"]]
        run([*clone, source, str(repo)], timeout=90)
        assert sorted(p.name for p in parent.iterdir()) == ["module"]
        actual_head = run(["git", "rev-parse", "HEAD"], repo).decode().strip()
        assert actual_head == prepared["head"]
        assert not run(["git", "status", "--porcelain"], repo)
        metadata = json.loads((repo / "repository.json").read_text())
        assert metadata["source_commit"] == prepared["source_commit"]
        assert metadata["release_tag"] == prepared["tag"]
        inventory = json.loads((repo / "repository-files.json").read_text())["files"]
        assert inventory == prepared["files"]
        for row in inventory:
            blob = subprocess.check_output(["git", "show", "HEAD:" + row["path"]], cwd=repo)
            assert len(blob) == row["bytes"] and hashlib.sha256(blob).hexdigest() == row["sha256"], row["path"]
            assert (repo / row["path"]).read_bytes() == blob, "checkout mismatch " + row["path"]
        result["inventory_files_verified"] = len(inventory)
        result["inventory_basis"] = "committed Git blobs and exact Linux checkout bytes"
        result["rustc"] = run(["rustc", "--version"]).decode().strip()
        for command in prepared["commands"]:
            run(command, repo)
        lock_bytes = (repo / "Cargo.lock").read_bytes()
        result["cargo_lock_sha256"] = hashlib.sha256(lock_bytes).hexdigest()
        packages = tomllib.loads(lock_bytes.decode())["package"]
        result["resolved_nextcore"] = [{k: p[k] for k in ["name", "version", "source"] if k in p}
                                      for p in packages if p["name"].startswith("nextcore-")]
        expected = {x["module"].lower(): x["head"] for x in json.loads((HERE / "prepared.json").read_text())["retained_unchanged"]}
        expected.update({s.lower(): json.loads((HERE / f"{s}-prepared.json").read_text())["head"] for s in ["Core", "EFI", "Tool"]})
        for pkg in result["resolved_nextcore"]:
            if "source" in pkg:
                assert pkg["source"].rsplit("#", 1)[-1] == expected[pkg["name"][len("nextcore-"):]], pkg
        if args.module == "EFI":
            binary = repo / "target/x86_64-unknown-uefi/debug/NXAPFS.efi"
            data = binary.read_bytes()
            assert data[:2] == b"MZ"
            pe = struct.unpack_from("<I", data, 0x3c)[0]
            assert pe + 24 + 70 <= len(data) and data[pe:pe + 4] == b"PE\0\0"
            machine = struct.unpack_from("<H", data, pe + 4)[0]
            magic = struct.unpack_from("<H", data, pe + 24)[0]
            subsystem = struct.unpack_from("<H", data, pe + 24 + 68)[0]
            entry_rva = struct.unpack_from("<I", data, pe + 24 + 16)[0]
            assert machine == 0x8664 and magic == 0x20b and subsystem == 10 and entry_rva != 0
            keep = mounted(json.loads((HERE / "prepared.json").read_text())["base"]) / "preserved-binaries" / args.phase
            keep.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(binary, keep / "NXAPFS.efi")
            result["nxapfs"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "machine": machine, "optional_magic": magic, "subsystem": subsystem,
                "entry_rva_nonzero": True, "preserved_path": str(keep / "NXAPFS.efi"), "executed": False}
        assert not run(["git", "status", "--porcelain"], repo)
        result["passed"] = True
    except Exception as failure:
        result["error"] = str(failure)
    finally:
        (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"module": args.module, "phase": args.phase, "passed": result["passed"],
                          "receipt": str(out / "receipt.json"), "error": result.get("error")}), flush=True)
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
