#!/usr/bin/env python3
"""Clean only finished, task-owned clone Cargo targets; preserve sources/logs/PE."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent


def size(path):
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def main():
    records = []
    env = os.environ.copy()
    env["PATH"] = "/home/developer/.cargo/bin:" + env["PATH"]
    env["CARGO_TERM_COLOR"] = "never"
    for phase in ["pre", "post"]:
        for short in ["Core", "EFI", "Tool"]:
            receipt = json.loads((HERE / "gates" / phase / short / "r1/receipt.json").read_text())
            assert receipt["passed"]
            parent = Path(receipt["single_repo_parent"]).resolve(strict=True)
            assert parent.parent == Path("/tmp") and parent.name.startswith(f"nextcore-apfs-release-{short.lower()}-{phase}-")
            repo = (parent / "module").resolve(strict=True)
            assert repo.parent == parent
            target = (repo / "target").resolve(strict=True)
            assert target.parent == repo and target.name == "target"
            if short == "EFI":
                kept = Path(receipt["nxapfs"]["preserved_path"])
                assert hashlib.sha256(kept.read_bytes()).hexdigest() == receipt["nxapfs"]["sha256"]
            before = size(target)
            command = ["cargo", "clean", "--profile", "dev", "--manifest-path", str(repo / "Cargo.toml"), "--target-dir", str(target)]
            begin = time.monotonic()
            result = subprocess.run(command, cwd=repo, env=env, capture_output=True, timeout=120)
            after = size(target)
            records.append({"module": short, "phase": phase, "checked_target": str(target), "argv": command,
                "exit_code": result.returncode, "stdout": result.stdout.decode(), "stderr": result.stderr.decode(),
                "before_bytes": before, "after_bytes": after, "elapsed_seconds": round(time.monotonic() - begin, 3)})
            assert result.returncode == 0
            assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=repo)
    receipt = {"only_task_owned_finished_targets": True, "records": records,
               "reclaimed_bytes": sum(r["before_bytes"] - r["after_bytes"] for r in records),
               "source_clones_logs_and_nxapfs_binaries_preserved": True}
    (HERE / "cleanup-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"targets": len(records), "reclaimed_bytes": receipt["reclaimed_bytes"]}))


if __name__ == "__main__":
    main()
