#!/usr/bin/env python3
"""Publish exported 26x86 module trees to GitHub.

Dry-run by default. Mutating GitHub/network actions run only with --apply.
Auth uses the ADGIT credential via environment (mapped to GH_TOKEN for the
gh subprocess) and the value is never printed, logged, or written into a
remote URL or file.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

OWNER = "26x86"
CORE_REPOSITORY = "26x86"
LEGACY_RELEASE_PREFIX = "26x86-VenFire-GoldenGate-v"


def legacy_tag_is_removable(tag: str) -> bool:
    return tag.startswith(LEGACY_RELEASE_PREFIX)


def load_exports(exports: Path) -> list[dict[str, object]]:
    plans = []
    for child in sorted(p for p in exports.iterdir() if p.is_dir()):
        meta_file = child / "repository.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        plans.append({"directory": str(child), "metadata": meta})
    if not plans:
        raise RuntimeError(f"no exported repositories found in {exports}")
    return plans


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)


def authenticated_owner() -> str:
    """Verify the caller is an active admin of the target organization."""
    user = run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    membership = run(["gh", "api", f"orgs/{OWNER}/memberships/{user}"])
    record = json.loads(membership.stdout)
    state, role = record.get("state"), record.get("role")
    if state != "active" or role != "admin":
        raise RuntimeError(
            f"authenticated user {user!r} is not an active admin of org {OWNER!r} "
            f"(state={state!r}, role={role!r}); refusing to publish")
    return OWNER


def plan_actions(plans: list[dict[str, object]]) -> list[str]:
    actions = []
    for item in plans:
        meta = item["metadata"]
        name = meta.get("name", "?")
        tag = meta.get("initial_tag", "?")
        actions.append(f"ensure public repo {OWNER}/{name} exists")
        actions.append(f"push {item['directory']} branch+tag {tag} to {OWNER}/{name}")
    actions.append(f"list core releases; remove only tags starting with {LEGACY_RELEASE_PREFIX!r} (with --apply)")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exports", required=True, type=Path)
    parser.add_argument("--apply", action="store_true",
                        help="perform GitHub mutations; without it, only print the plan")
    args = parser.parse_args()

    exports = args.exports.absolute()
    plans = load_exports(exports)
    for line in plan_actions(plans):
        print(line)

    if not args.apply:
        print(json.dumps({"exports": str(exports), "applied": False,
                          "repositories": [p["metadata"].get("name") for p in plans]}, indent=2))
        return 0

    token = os.environ.get("ADGIT")
    if not token:
        raise RuntimeError("ADGIT credential is required for --apply")
    env = dict(os.environ)
    env["GH_TOKEN"] = token

    owner = authenticated_owner()
    if owner != OWNER:
        raise RuntimeError(f"authenticated owner {owner!r} != expected {OWNER!r}; refusing to publish")

    report: list[dict[str, object]] = []
    for item in plans:
        meta = item["metadata"]
        name = str(meta.get("name"))
        directory = Path(str(item["directory"]))
        tag = str(meta.get("initial_tag", ""))
        subprocess.run(["gh", "repo", "create", f"{OWNER}/{name}",
                        "--public", "--disable-wiki", "--disable-issues"],
                       capture_output=True, text=True, env=env)
        branch = subprocess.run(["git", "-C", str(directory), "branch", "--show-current"],
                                capture_output=True, text=True, check=True).stdout.strip() or "main"
        subprocess.run(["git", "-C", str(directory), "push", f"https://github.com/{OWNER}/{name}.git",
                        f"{branch}:main", tag], check=True, capture_output=True, text=True, env=env)
        report.append({"repository": f"{OWNER}/{name}", "pushed_tag": tag})

    releases = subprocess.run(["gh", "release", "list", "--repo", f"{OWNER}/{CORE_REPOSITORY}",
                               "--limit", "200", "--json", "tagName"],
                              capture_output=True, text=True, env=env, check=True)
    removed = []
    for entry in json.loads(releases.stdout or "[]"):
        tag = str(entry.get("tagName", ""))
        if legacy_tag_is_removable(tag):
            subprocess.run(["gh", "release", "delete", tag, "--yes", "--cleanup-tag",
                            "--repo", f"{OWNER}/{CORE_REPOSITORY}"],
                           check=True, capture_output=True, text=True, env=env)
            removed.append(tag)
    print(json.dumps({"exports": str(exports), "applied": True,
                      "pushed": report, "removed_legacy_releases": removed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
