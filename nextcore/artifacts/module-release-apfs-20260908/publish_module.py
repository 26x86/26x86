"""Atomically publish one already committed, Linux-validated incremental release."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("module", choices=["Core", "EFI", "Tool"])
    args = ap.parse_args()
    prepared = json.loads((HERE / f"{args.module}-prepared.json").read_text())
    gate = json.loads((HERE / "gates/pre" / args.module / "r1/receipt.json").read_text())
    assert gate["passed"] and gate["expected_head"] == prepared["head"]
    assert gate["source_commit"] == prepared["source_commit"]
    repo = Path(prepared["path"])

    def git(*argv):
        p = subprocess.run(["git", *argv], cwd=repo, capture_output=True, timeout=90)
        if p.returncode:
            raise RuntimeError(repr(argv) + ": " + p.stderr.decode(errors="replace"))
        return p.stdout

    def refs():
        return {line.split()[1]: line.split()[0] for line in git("ls-remote", "--heads", "--tags", "origin").decode().splitlines()}

    assert not git("status", "--porcelain")
    assert git("rev-parse", "HEAD").decode().strip() == prepared["head"]
    assert git("rev-parse", "HEAD^").decode().strip() == prepared["previous_head"]
    for row in prepared["files"]:
        content = git("show", "HEAD:" + row["path"])
        assert len(content) == row["bytes"] and hashlib.sha256(content).hexdigest() == row["sha256"]
    before = refs()
    assert before["refs/heads/main"] == prepared["previous_head"]
    for ref, head in prepared["old_refs"].items():
        if ref.startswith("refs/tags/"):
            assert before[ref] == head, "old tag moved: " + ref
    assert "refs/tags/" + prepared["tag"] not in before
    git("tag", prepared["tag"], prepared["head"])
    git("push", "--atomic", "origin", "HEAD:refs/heads/main", "refs/tags/" + prepared["tag"])
    after = refs()
    assert after["refs/heads/main"] == after["refs/tags/" + prepared["tag"]] == prepared["head"]
    assert all(after.get(ref) == head for ref, head in before.items() if ref.startswith("refs/tags/"))
    result = {"module": args.module, "repository": prepared["repository"],
        "source_commit": prepared["source_commit"], "head": prepared["head"],
        "previous_head": prepared["previous_head"], "tag": prepared["tag"],
        "pre_linux_gate_passed": True, "atomic_push": True, "force_push": False,
        "old_tags_preserved": True, "main_and_tag_match": True, "refs_after": after}
    (HERE / f"{args.module}-published.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
