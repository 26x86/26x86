"""Prepare public immutable-source incremental commits. No tag or push command."""
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import tomllib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = "65d1e85db2dfcd4e1c07656bb0bfc315d36fac83"
RELEASES = {"Core": "0.1.2", "EFI": "0.1.2", "Tool": "0.1.3"}
PINS = {**RELEASES, "GPU": "0.1.1", "HAL": "0.1.1", "ISE": "0.1.1", "APLS": "0.1.1"}
DEPS = {"Core": [], "EFI": ["Core"], "Tool": ["Core", "APLS"]}
GENERATED = {".gitignore", ".gitattributes", ".github/workflows/ci.yml", "README.md", "LICENSE.txt", "repository.json", "repository-files.json"}
DENIED = {"_isolated", "artifacts", "target", ".git"}


def run(argv, cwd=None):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=90)
    if p.returncode:
        raise RuntimeError(repr(argv) + ": " + p.stderr.decode(errors="replace"))
    return p.stdout


def git(repo, *args):
    return run(["git", *args], repo)


def safe(path):
    p = PurePosixPath(path)
    if p.is_absolute() or not p.parts or any(x in (".", "..") or x.lower() in DENIED for x in p.parts):
        raise ValueError("prohibited path: " + path)
    return p


def tag(short):
    return f"26x86-Nextcore-{short}-v{PINS[short]}"


def commands(short):
    if short == "EFI":
        return [["cargo", "check", "--target", "x86_64-unknown-uefi", "--all-features"],
                ["cargo", "build", "--target", "x86_64-unknown-uefi", "--all-features", "--bin", "NXAPFS"]]
    result = [["cargo", "test", "--all-targets"]]
    if short == "Core":
        result += [["cargo", "test", "--no-default-features", "--test", "apfs_jumpstart"],
                   ["cargo", "check", "--no-default-features", "--lib", "--target", "x86_64-unknown-uefi"]]
    return result


def workflow(short):
    steps = (["rustup", "target", "add", "x86_64-unknown-uefi"],) if short in ("Core", "EFI") else ()
    return (f"name: NextCore {short} CI\non:\n  push:\n  pull_request:\n  workflow_dispatch:\n"
            "permissions:\n  contents: read\njobs:\n  verify:\n    runs-on: ubuntu-24.04\n    steps:\n"
            "      - uses: actions/checkout@v4\n      - uses: dtolnay/rust-toolchain@stable\n" +
            "".join("      - run: " + " ".join(c) + "\n" for c in [*steps, *commands(short)])).encode()


def source_blob(path):
    return git(ROOT, "show", f"{SOURCE}:{path}")


def main():
    if (HERE / "prepared.json").exists():
        raise RuntimeError("preparation receipt exists; do not overwrite")
    assert git(ROOT, "rev-parse", SOURCE + "^{commit}").decode().strip() == SOURCE
    before = json.loads((HERE.parent / "module-release-apfs-prep-20260908/remote-observation.json").read_text())
    before = {x["repository"].split("-")[-1]: x for x in before["modules"]}
    unchanged = []
    for short in ("GPU", "HAL", "ISE", "APLS"):
        path = "nextcore/crates/nextcore-" + short.lower()
        prior_tree = git(ROOT, "rev-parse", before[short]["source_commit"] + ":" + path).decode().strip()
        current_tree = git(ROOT, "rev-parse", SOURCE + ":" + path).decode().strip()
        assert prior_tree == current_tree, "unexpected changed retained crate: " + short
        unchanged.append({"module": short, "source_tree": current_tree, "head": before[short]["head"], "tag": before[short]["current_release_tag"]})
    base = Path(tempfile.mkdtemp(prefix="nextcore-modules-apfs-20260908-"))
    records = []
    for short, version in RELEASES.items():
        name = "Nextcore-" + short
        repo = base / name
        run(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "clone",
             "--config", "core.autocrlf=false", "--config", "core.eol=lf",
             f"https://github.com/26x86/{name}.git", str(repo)])
        old_head = git(repo, "rev-parse", "HEAD").decode().strip()
        assert old_head == before[short]["head"]
        assert not git(repo, "status", "--porcelain")
        assert not git(repo, "ls-remote", "origin", "refs/tags/" + tag(short))
        old_meta = json.loads(git(repo, "show", "HEAD:repository.json"))
        old_inventory = json.loads(git(repo, "show", "HEAD:repository-files.json"))
        managed = {r["path"] for r in old_inventory["files"]} | GENERATED
        old_tracked = git(repo, "ls-files", "-z").decode().split("\0")[:-1]
        payload = {p: git(repo, "show", "HEAD:" + p) for p in old_tracked if p not in managed}
        source_rows = []
        prefix = "nextcore/crates/nextcore-" + short.lower() + "/"
        for record in git(ROOT, "ls-tree", "-r", "-z", SOURCE, "--", prefix).split(b"\0")[:-1]:
            fields, full = record.split(b"\t", 1)
            mode, kind, oid = fields.decode().split()
            full = full.decode()
            assert kind == "blob" and mode in ("100644", "100755") and full.startswith(prefix)
            relative = full[len(prefix):]
            safe(relative)
            assert relative not in GENERATED, "source/generated collision: " + relative
            content = source_blob(full)
            payload[relative] = content
            source_rows.append({"path": relative, "source_path": full, "mode": mode, "git_blob": oid,
                                "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
        assert source_rows
        original_manifest = tomllib.loads(payload["Cargo.toml"].decode())
        actual_deps = {x for x in original_manifest.get("dependencies", {}) if x.startswith("nextcore-")}
        assert actual_deps == {"nextcore-" + x.lower() for x in DEPS[short]}
        manifest = payload["Cargo.toml"].decode()
        for dep in DEPS[short]:
            expression = r'(nextcore-' + dep.lower() + r'\s*=\s*\{\s*)path\s*=\s*"\.\./nextcore-' + dep.lower() + r'"'
            manifest, count = re.subn(expression, lambda m: m[1] + f'git = "https://github.com/26x86/Nextcore-{dep}.git", tag = "{tag(dep)}"', manifest)
            assert count == 1
        assert not re.search(r'path\s*=\s*"\.\./nextcore-', manifest)
        payload["Cargo.toml"] = manifest.encode()
        final_manifest = tomllib.loads(manifest)
        assert original_manifest["package"] == final_manifest["package"]
        if short == "EFI":
            nx = [b for b in final_manifest["bin"] if b["name"] == "NXAPFS"]
            assert len(nx) == 1 and nx[0]["path"] == "src/apfs_probe.rs" and nx[0]["required-features"] == ["apfs-jumpstart"]
        if short == "Tool":
            assert b'include_bytes!("data/sample.plist")' in payload["tests/bundle_cli.rs"]
            assert "tests/data/sample.plist" in payload
        payload["LICENSE.txt"] = source_blob("LICENSE.txt")
        payload[".gitignore"] = b"/target/\nCargo.lock\n"
        payload[".gitattributes"] = b"* text=auto\n*.S text eol=lf\n"
        payload[".github/workflows/ci.yml"] = workflow(short)
        description = {"Core": "Public boot configuration and bounded format codecs, including APFS Jumpstart extraction.",
                       "EFI": "UEFI boot selection, platform services and explicit APFS Jumpstart driver loading.",
                       "Tool": "Command-line preparation and orchestration with independently pinned NextCore modules."}[short]
        readme = f"# NextCore {short}\n\n{description}\n\nSource snapshot: [{SOURCE}](https://github.com/26x86/26x86/commit/{SOURCE}).\n\nRepository release: `{tag(short)}`. Cargo package version is preserved from source.\n\n"
        readme += "Public source only; no Apple firmware, filesystem driver payload, operating-system image or private research input is bundled. Module checks establish their stated source/build boundary; they do not establish installed macOS boot, guest Metal or physical hardware support.\n"
        if DEPS[short]:
            readme += "\n## Fixed dependencies\n\n" + "".join(f"- [{d}](https://github.com/26x86/Nextcore-{d}/tree/{tag(d)})\n" for d in DEPS[short])
        payload["README.md"] = readme.encode()
        for path in payload:
            safe(path)
        for path in managed - set(payload):
            safe(path)
            target = repo / path
            if target.exists():
                assert target.is_file() and target.resolve().is_relative_to(repo.resolve())
                target.unlink()
        for path, content in payload.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        meta = dict(old_meta)
        meta.update(source_commit=SOURCE, release_tag=tag(short), previous_head=old_head,
                    description=description, generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    dependency_tags={f"26x86/Nextcore-{d}": tag(d) for d in DEPS[short]},
                    export_method="immutable git objects applied to existing main; manifest dependency rewrite only")
        rows = [{"path": p, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} for p, b in sorted(payload.items())]
        (repo / "repository.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        (repo / "repository-files.json").write_text(json.dumps({"schema": "26x86.repository-files/1", "files": rows}, indent=2) + "\n", encoding="utf-8")
        git(repo, "add", "-A")
        for row in source_rows:
            git(repo, "update-index", "--chmod=" + ("+x" if row["mode"] == "100755" else "-x"), "--", row["path"])
        assert set(git(repo, "ls-files", "-z").decode().split("\0")[:-1]) == set(payload) | {"repository.json", "repository-files.json"}
        for row in rows:
            assert hashlib.sha256(git(repo, "show", ":" + row["path"])).hexdigest() == row["sha256"]
        git(repo, "-c", "user.name=26x86 release tooling", "-c", "user.email=release@26x86.local",
            "commit", "-m", f"Release NextCore {short} v{version} from {SOURCE[:7]}")
        head = git(repo, "rev-parse", "HEAD").decode().strip()
        assert git(repo, "rev-parse", "HEAD^").decode().strip() == old_head
        assert not git(repo, "status", "--porcelain")
        record = {"module": short, "repository": "26x86/" + name, "path": str(repo), "source_commit": SOURCE,
                  "head": head, "previous_head": old_head, "tag": tag(short), "dependencies": meta["dependency_tags"],
                  "commands": commands(short), "source_files": source_rows, "files": rows,
                  "old_refs": before[short]["refs"], "transformed_source_files": ["Cargo.toml"] if DEPS[short] else [],
                  "package_version_preserved": True, "pushed": False}
        records.append(record)
        (HERE / f"{short}-prepared.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: record[k] for k in ["module", "head", "tag"]}), flush=True)
    (HERE / "prepared.json").write_text(json.dumps({"source_commit": SOURCE, "base": str(base),
        "modules": [{k: x[k] for k in ["module", "head", "tag", "path"]} for x in records],
        "retained_unchanged": unchanged, "remote_mutations": []}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
