"""Publish reviewed organization copy only after all release and clone gates."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    ci = json.loads((HERE / "ci-latest.json").read_text())
    assert ci["passed"]
    for short in ["Core", "EFI", "Tool"]:
        for phase in ["pre", "post"]:
            assert json.loads((HERE / "gates" / phase / short / "r1/receipt.json").read_text())["passed"]
    prepared = json.loads((HERE / "profile-prepared.json").read_text())
    repo = Path(prepared["path"])

    def git(*args):
        p = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=60)
        if p.returncode:
            raise RuntimeError(p.stderr.decode(errors="replace"))
        return p.stdout

    assert git("rev-parse", "HEAD").decode().strip() == prepared["previous_head"]
    assert git("ls-remote", "origin", "refs/heads/main").decode().split()[0] == prepared["previous_head"]
    assert git("diff", "--name-only").decode().splitlines() == ["profile/README.md"]
    contents = (repo / "profile/README.md").read_bytes()
    assert hashlib.sha256(contents).hexdigest() == prepared["file_sha256"]
    assert contents == (HERE / "profile-draft.md").read_bytes()
    git("add", "--", "profile/README.md")
    assert git("diff", "--cached", "--name-only").decode().splitlines() == ["profile/README.md"]
    git("-c", "user.name=26x86 release tooling", "-c", "user.email=release@26x86.local",
        "commit", "-m", "Update NextCore APFS module releases and execution evidence")
    head = git("rev-parse", "HEAD").decode().strip()
    assert git("rev-parse", "HEAD^").decode().strip() == prepared["previous_head"]
    git("push", "origin", "HEAD:refs/heads/main")
    assert git("ls-remote", "origin", "refs/heads/main").decode().split()[0] == head
    assert not git("status", "--porcelain")
    readback = json.loads(subprocess.check_output(["gh", "api", f"repos/26x86/.github/contents/profile/README.md?ref={head}"], timeout=60))
    assert base64.b64decode(readback["content"]) == contents
    receipt = {"repository": "26x86/.github", "head": head, "previous_head": prepared["previous_head"],
        "source_commit": prepared["source_commit"], "file_sha256": prepared["file_sha256"],
        "remote_blob": readback["sha"], "api_readback_matches": True, "force_push": False,
        "all_release_pre_post_ci_passed": True, "independent_review": "hal_harness: no confirmed blocker; post gates required and completed"}
    (HERE / "profile-published.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
