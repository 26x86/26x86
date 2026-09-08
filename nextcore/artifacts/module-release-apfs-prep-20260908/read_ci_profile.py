"""Read exact-head CI and organization profile; never mutate remote state."""
import base64
import concurrent.futures
import datetime
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent


def run(argv):
    return subprocess.check_output(argv, timeout=60)


def api(endpoint):
    return json.loads(run(["gh", "api", endpoint]))


def ci(module):
    data = api(f"repos/{module['repository']}/actions/runs?head_sha={module['head']}&per_page=10")
    return {"repository": module["repository"], "expected_head": module["head"],
            "runs": [{key: item[key] for key in ["id", "head_sha", "status", "conclusion", "html_url"]}
                     for item in data["workflow_runs"]]}


def main():
    modules = json.loads((HERE / "remote-observation.json").read_text())["modules"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        checks = list(pool.map(ci, modules))
    head = run(["git", "ls-remote", "https://github.com/26x86/.github.git",
                "refs/heads/main"]).decode().split()[0]
    data = api(f"repos/26x86/.github/contents/profile/README.md?ref={head}")
    result = {"observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "read_only": True, "remote_mutations": [], "ci": checks,
              "profile": {"head": head, "blob": data["sha"],
                          "text": base64.b64decode(data["content"]).decode()}}
    (HERE / "ci-profile-observation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"profile_head": head, "ci": [{"repository": c["repository"],
        "conclusions": [r["conclusion"] for r in c["runs"]]} for c in checks]}))


if __name__ == "__main__":
    main()
