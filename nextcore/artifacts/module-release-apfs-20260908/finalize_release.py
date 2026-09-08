"""Recheck seven remote histories and collect completed APFS release evidence."""
import concurrent.futures
import datetime
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    prepared = json.loads((HERE / "prepared.json").read_text())
    old = json.loads((HERE.parent / "module-release-apfs-prep-20260908/remote-observation.json").read_text())["modules"]
    ci = json.loads((HERE / "ci-latest.json").read_text())
    assert ci["passed"]
    published = {s: json.loads((HERE / f"{s}-published.json").read_text()) for s in ["Core", "EFI", "Tool"]}

    def audit(item):
        short = item["repository"].rsplit("-", 1)[1]
        output = subprocess.check_output(["git", "ls-remote", "--heads", "--tags", f"https://github.com/{item['repository']}.git"], timeout=60).decode()
        refs = {line.split()[1]: line.split()[0] for line in output.splitlines()}
        expected_head = published[short]["head"] if short in published else item["head"]
        release_tag = published[short]["tag"] if short in published else item["current_release_tag"]
        assert refs["refs/heads/main"] == refs["refs/tags/" + release_tag] == expected_head
        assert all(refs.get(ref) == head for ref, head in item["refs"].items() if ref.startswith("refs/tags/"))
        return {"repository": item["repository"], "head": expected_head, "tag": release_tag,
                "released_now": short in published, "all_previous_tags_preserved": True, "refs": refs}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        remote = list(pool.map(audit, old))
    modules = []
    for short, publication in published.items():
        phases = {}
        for phase in ["pre", "post"]:
            directory = HERE / "gates" / phase / short / "r1"
            gate = json.loads((directory / "receipt.json").read_text())
            assert gate["passed"] and gate["expected_head"] == publication["head"]
            results = []
            for command in gate["commands"]:
                summaries = re.findall(r"test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored", (directory / command["stdout"]).read_text())
                if summaries:
                    results.append({"argv": command["argv"], "passed": sum(int(x[0]) for x in summaries),
                        "failed": sum(int(x[1]) for x in summaries), "ignored": sum(int(x[2]) for x in summaries)})
            phases[phase] = {"receipt": str((directory / "receipt.json").relative_to(HERE)), "passed": True,
                "single_repo_parent": gate["single_repo_parent"], "test_summaries": results,
                "inventory_files_verified": gate["inventory_files_verified"], "cargo_lock_sha256": gate["cargo_lock_sha256"],
                "nxapfs": gate.get("nxapfs")}
        assert phases["pre"]["single_repo_parent"] != phases["post"]["single_repo_parent"]
        actions = next(x for x in ci["modules"] if x["module"] == short)
        modules.append({**publication, "gates": phases, "github_actions": actions})
    profile = json.loads((HERE / "profile-published.json").read_text())
    profile_head = subprocess.check_output(["git", "ls-remote", "https://github.com/26x86/.github.git", "refs/heads/main"], timeout=60).decode().split()[0]
    assert profile_head == profile["head"] and profile["api_readback_matches"]
    cleanup = json.loads((HERE / "cleanup-receipt.json").read_text())
    final = {"passed": True, "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "layer": "public module snapshot release and organization profile", "source_commit": prepared["source_commit"],
        "modules": modules, "all_seven_remote_audit": remote, "retained_source_subtrees": prepared["retained_unchanged"],
        "organization_profile": profile, "cargo_generated_bytes_reclaimed": cleanup["reclaimed_bytes"],
        "working_tree_source_used": False, "shared_index_modified": False, "private_assets_exported": False,
        "release_binaries_executed": False, "installed_os_boot_claimed": False, "metal_verified": False}
    (HERE / "release-receipt.json").write_text(json.dumps(final, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "modules": [{"module": m["module"], "head": m["head"],
        "tests": m["gates"]["post"]["test_summaries"], "nxapfs": m["gates"]["post"]["nxapfs"]} for m in modules],
        "profile_head": profile_head, "reclaimed_bytes": cleanup["reclaimed_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
