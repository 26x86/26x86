"""Read-only remote release audit. No clone, tag, commit, push or local index use."""
import base64
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
MODULES = ["Core", "GPU", "HAL", "ISE", "APLS", "EFI", "Tool"]


def run(argv):
    result = subprocess.run(argv, capture_output=True, check=True, timeout=60)
    return result.stdout


def api(endpoint):
    return json.loads(run(["gh", "api", endpoint]))


def inspect(short):
    repo = f"26x86/Nextcore-{short}"
    refs = {}
    for line in run(["git", "ls-remote", "--heads", "--tags",
                     f"https://github.com/{repo}.git"]).decode().splitlines():
        sha, ref = line.split()
        refs[ref] = sha
    head = refs["refs/heads/main"]
    files = {}
    for path in ["Cargo.toml", "repository.json", ".github/workflows/ci.yml"]:
        item = api(f"repos/{repo}/contents/{path}?ref={head}")
        content = base64.b64decode(item["content"])
        files[path] = {"git_blob": item["sha"], "sha256": hashlib.sha256(content).hexdigest(),
                       "text": content.decode()}
    metadata = json.loads(files["repository.json"]["text"])
    cargo = tomllib.loads(files["Cargo.toml"]["text"])
    dependencies = {}
    for section in ["dependencies", "dev-dependencies", "build-dependencies"]:
        for name, spec in cargo.get(section, {}).items():
            if name.startswith("nextcore-"):
                dependencies[name] = {"section": section, **spec}
    proposed = f"26x86-Nextcore-{short}-v0.1.{3 if short == 'Tool' else 2}"
    current_tag = metadata["release_tag"]
    resolved = refs.get("refs/tags/" + current_tag + "^{}", refs.get("refs/tags/" + current_tag))
    return {
        "repository": repo, "head": head, "refs": refs,
        "current_release_tag": current_tag, "current_tag_matches_main": resolved == head,
        "source_commit": metadata["source_commit"], "package_version": cargo["package"]["version"],
        "dependencies": dependencies, "features": cargo.get("features", {}),
        "bins": cargo.get("bin", []), "proposed_tag_if_released": proposed,
        "proposed_tag_unused": "refs/tags/" + proposed not in refs,
        "files": files,
    }


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        modules = list(pool.map(inspect, MODULES))
    result = {
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "read_only": True, "remote_mutations": [], "final_source_commit": None,
        "modules": modules,
    }
    (HERE / "remote-observation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for item in modules:
        print(json.dumps({key: item[key] for key in ["repository", "head", "current_release_tag",
            "source_commit", "dependencies", "proposed_tag_if_released", "proposed_tag_unused"]}))


if __name__ == "__main__":
    main()
