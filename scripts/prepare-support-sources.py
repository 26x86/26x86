#!/usr/bin/env python3
"""Fetch pinned support sources and apply the reviewed integration diffs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New source workspace, never an existing checkout")
    args = parser.parse_args()
    output = Path(args.output).expanduser().absolute()
    if output.exists() or output.is_symlink():
        parser.error("Output must not exist")
    sources = json.loads((ROOT / "integration/sources.lock.json").read_text())
    patches = json.loads((ROOT / "integration/support-patch-report.json").read_text())
    patch_map = {item["repository"]: item for item in patches}
    # Inspect all local diffs before starting any fetch or checkout.
    for item in patches:
        patch = (ROOT / item["patch"]).resolve()
        if ROOT not in patch.parents or hashlib.sha256(patch.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Support patch identity mismatch")
    output.mkdir(parents=True)
    for pin in sources["repositories"]:
        name = pin["name"]
        if name not in patch_map:
            continue
        if name not in {"26x86-OpenCorePkg", "26x86-PatcherSupportPkg", "26x86-MetallibSupportPkg"}:
            raise ValueError("Unknown support repository")
        directory = output / name
        subprocess.run(["git", "clone", "--no-checkout", pin["url"], str(directory)], check=True)
        subprocess.run(["git", "-C", str(directory), "checkout", "--detach", pin["commit"]], check=True)
        for license in pin["licenses"]:
            raw = subprocess.check_output(["git", "-C", str(directory), "show", pin["commit"] + ":" + license["path"]])
            if hashlib.sha256(raw).hexdigest() != license["sha256"]:
                raise ValueError("Pinned license identity mismatch")
        patch = ROOT / patch_map[name]["patch"]
        subprocess.run(["git", "-C", str(directory), "apply", "--check", str(patch)], check=True)
        subprocess.run(["git", "-C", str(directory), "apply", str(patch)], check=True)
        print(f"Prepared {name} at {pin['commit']}")


if __name__ == "__main__":
    main()
