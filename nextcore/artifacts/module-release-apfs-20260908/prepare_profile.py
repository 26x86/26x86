"""Prepare an existing-history organization-profile update, without pushing."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = "65d1e85db2dfcd4e1c07656bb0bfc315d36fac83"
PREVIOUS_SOURCE = "dcc90013109eac694ccbf997b1e44a7018480f78"


def main():
    base = Path(json.loads((HERE / "prepared.json").read_text())["base"])
    repo = base / "organization-profile"
    subprocess.run(["git", "clone", "--config", "core.autocrlf=false", "--config", "core.eol=lf",
                    "https://github.com/26x86/.github.git", str(repo)], check=True, capture_output=True, timeout=60)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, timeout=30)

    previous = git("rev-parse", "HEAD").decode().strip()
    assert previous == "4e446a4b7debc714ff2ec7ac6ead069bb2860618"
    assert not git("status", "--porcelain")
    path = repo / "profile/README.md"
    original = git("show", "HEAD:profile/README.md").decode().replace("\r\n", "\n").replace("\r", "\n")
    text = original.replace(PREVIOUS_SOURCE, SOURCE)
    text = text.replace(
        "| Golden Gate ARM64E |",
        f"| APFS EFI driver | [Original driver extraction, StartImage and controller connection succeeded](https://github.com/26x86/26x86/blob/{SOURCE}/nextcore/artifacts/apfs-firmware-20260908/original-apfs-result.json) | Filesystem opening and installed-OS boot verification |\n| Golden Gate ARM64E |", 1)
    old = ("The `v0.1.1` snapshots use the source commit above. Tool `v0.1.2` includes a\n"
           "[crate-local test-fixture correction](https://github.com/26x86/26x86/commit/045065700cbd037eaaa974faf957ba15cb628370).\n")
    new = ("Core/EFI `v0.1.2` and Tool `v0.1.3` use the source commit above. GPU, HAL,\n"
           f"ISE and APLS retain their [original `v0.1.1` source](https://github.com/26x86/26x86/tree/{PREVIOUS_SOURCE}).\n"
           "Tool retains its [crate-local test-fixture correction](https://github.com/26x86/26x86/commit/045065700cbd037eaaa974faf957ba15cb628370).\n"
           "The three updated modules passed independent Linux clone gates before and after\n"
           "publishing; EFI additionally linked the NXAPFS application. Exact release-head CI\n"
           "also passed. The linked module build is not itself an execution test.\n")
    assert old in text
    text = text.replace(old, new)
    for short, old_version in [("Core", "0.1.1"), ("EFI", "0.1.1"), ("Tool", "0.1.2")]:
        p = json.loads((HERE / f"{short}-published.json").read_text())
        version = p["tag"].rsplit("-v", 1)[1]
        old_link = f"[v{old_version}](https://github.com/26x86/Nextcore-{short}/tree/26x86-Nextcore-{short}-v{old_version})"
        new_link = f"[v{version}](https://github.com/26x86/Nextcore-{short}/tree/{p['tag']}) · [{p['head'][:7]}](https://github.com/26x86/Nextcore-{short}/commit/{p['head']})"
        assert text.count(old_link) == 1
        text = text.replace(old_link, new_link)
    for link in ["nextcore-logo-256.png", "https://github.com/26x86/OpenCorePkg",
                 "https://github.com/26x86/MetallibSupportPkg", "https://github.com/26x86/PatcherSupportPkg",
                 "https://github.com/26x86/VenFire", "metal_verified=false"]:
        assert link in original and link in text
    path.write_text(text, encoding="utf-8", newline="\n")
    (HERE / "profile-draft.md").write_bytes(path.read_bytes())
    (HERE / "profile-prepared.json").write_text(json.dumps({"path": str(repo), "previous_head": previous,
        "source_commit": SOURCE, "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "pushed": False}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(repo), "previous_head": previous, "pushed": False}))


if __name__ == "__main__":
    main()
