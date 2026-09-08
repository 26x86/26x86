#!/usr/bin/env python3
"""Export clean-room Nextcore crates as independently versioned Git repositories.

The command writes only a new output directory.  It never alters the source
checkout, creates GitHub repositories, or pushes a remote.  The caller may
publish the initialized output repositories after reviewing their inventories.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CRATES = ROOT / "nextcore" / "crates"
OWNER = "26x86"
VERSION = "v0.1.0"
MODULES = (
    ("Nextcore-Core", "nextcore-core", "core boot configuration and public format codecs", (), "test"),
    ("Nextcore-GPU", "nextcore-gpu", "GPU compatibility policy and virtual-device contracts", (), "test"),
    ("Nextcore-HAL", "nextcore-hal", "ACPI, PCI, SMBIOS and DeviceTree translation layer", (), "test"),
    ("Nextcore-ISE", "nextcore-ise", "instruction-set emulation and CPU feature policy", (), "test"),
    ("Nextcore-APLS", "nextcore-apls", "AArch64 VMApple recovery runner and guest ABI", ("Nextcore-GPU",), "test"),
    ("Nextcore-EFI", "nextcore-efi", "UEFI application and controlled XNU handoff probe", ("Nextcore-Core",), "uefi-check"),
    ("Nextcore-Tool", "nextcore-tool", "Nextcore command-line orchestration", ("Nextcore-Core", "Nextcore-APLS"), "test"),
)


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def tag(name: str) -> str:
    return f"26x86-{name}-{VERSION}"


def tracked_files(crate: str) -> list[Path]:
    prefix = f"nextcore/crates/{crate}/"
    files = run("git", "-C", str(ROOT), "ls-files", "--", prefix).splitlines()
    if not files:
        raise RuntimeError(f"crate has no tracked files: {crate}")
    result = [ROOT / entry for entry in files]
    for path in result:
        if not path.is_file() or "_isolated" in path.parts:
            raise RuntimeError(f"invalid public export input: {path}")
    return result


def copy_crate(crate: str, destination: Path) -> None:
    source_root = CRATES / crate
    for source in tracked_files(crate):
        relative = source.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def rewrite_dependencies(manifest: Path) -> None:
    text = manifest.read_text(encoding="utf-8")
    replacements = {
        'nextcore-core = { path = "../nextcore-core" }':
            f'nextcore-core = {{ git = "https://github.com/{OWNER}/Nextcore-Core.git", tag = "{tag("Nextcore-Core")}" }}',
        'nextcore-core = { path = "../nextcore-core", default-features = false }':
            f'nextcore-core = {{ git = "https://github.com/{OWNER}/Nextcore-Core.git", tag = "{tag("Nextcore-Core")}", default-features = false }}',
        'nextcore-gpu = { path = "../nextcore-gpu" }':
            f'nextcore-gpu = {{ git = "https://github.com/{OWNER}/Nextcore-GPU.git", tag = "{tag("Nextcore-GPU")}" }}',
        'nextcore-apls = { path = "../nextcore-apls" }':
            f'nextcore-apls = {{ git = "https://github.com/{OWNER}/Nextcore-APLS.git", tag = "{tag("Nextcore-APLS")}" }}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if 'path = "../nextcore-' in text:
        raise RuntimeError(f"unrewritten Nextcore dependency in {manifest}")
    manifest.write_text(text, encoding="utf-8")


def inventory(destination: Path) -> list[dict[str, object]]:
    entries = []
    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        relative = path.relative_to(destination).as_posix()
        if relative in {"repository.json", "repository-files.json"}:
            continue
        entries.append({"path": relative, "bytes": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return entries


def write_files(destination: Path, name: str, crate: str, description: str,
                dependencies: tuple[str, ...], build: str) -> None:
    (destination / "LICENSE.txt").write_bytes((ROOT / "LICENSE.txt").read_bytes())
    (destination / ".gitignore").write_text("/target/\nCargo.lock\n", encoding="utf-8")
    (destination / ".gitattributes").write_text("* text=auto\n*.S text eol=lf\n", encoding="utf-8")
    dependency_links = "\n".join(f"- [{dep}](https://github.com/{OWNER}/{dep})" for dep in dependencies)
    readme = (
        f"# {name}\n\n"
        f"{description}. This is the `{crate}` clean-room module from "
        f"[26x86](https://github.com/{OWNER}/26x86).\n\n"
        "It contains no Apple firmware, operating-system binaries, or private research inputs. "
        "Passing its tests is module-level evidence, not a macOS boot claim.\n"
    )
    if dependency_links:
        readme += f"\n## Fixed module dependencies\n\n{dependency_links}\n"
    (destination / "README.md").write_text(readme, encoding="utf-8")
    command = "cargo test --all-targets" if build == "test" else "rustup target add x86_64-unknown-uefi && cargo check --target x86_64-unknown-uefi"
    workflow = (
        f"name: {name} CI\n"
        "on:\n  push:\n  pull_request:\n  workflow_dispatch:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  verify:\n    runs-on: ubuntu-24.04\n"
        "    steps:\n      - uses: actions/checkout@v4\n"
        "      - uses: dtolnay/rust-toolchain@stable\n"
        f"      - run: {command}\n"
    )
    ci = destination / ".github" / "workflows" / "ci.yml"
    ci.parent.mkdir(parents=True, exist_ok=True)
    ci.write_text(workflow, encoding="utf-8")
    metadata = {
        "schema": "26x86.repository/1", "name": name, "owner": OWNER, "public": True,
        "role": "nextcore-module", "crate": crate, "description": description,
        "source_path": f"nextcore/crates/{crate}",
        "source_commit": run("git", "-C", str(ROOT), "rev-parse", "HEAD"),
        "depends_on": [f"{OWNER}/{item}" for item in dependencies],
        "initial_tag": tag(name), "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (destination / "repository.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (destination / "repository-files.json").write_text(
        json.dumps({"schema": "26x86.repository-files/1", "files": inventory(destination)}, indent=2) + "\n",
        encoding="utf-8")


def init_repository(destination: Path, name: str) -> None:
    run("git", "-C", str(destination), "init", "-b", "main")
    run("git", "-C", str(destination), "add", "-A")
    run("git", "-C", str(destination), "-c", "user.name=26x86 release tooling",
        "-c", "user.email=release@26x86.local", "commit", "-m", f"Initial module export ({tag(name)})")
    run("git", "-C", str(destination), "tag", tag(name))


def export(output: Path) -> list[dict[str, str]]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"output must be fresh: {output}")
    output.mkdir(parents=True)
    result = []
    for name, crate, description, dependencies, build in MODULES:
        destination = output / name
        destination.mkdir()
        copy_crate(crate, destination)
        rewrite_dependencies(destination / "Cargo.toml")
        write_files(destination, name, crate, description, dependencies, build)
        init_repository(destination, name)
        result.append({"repository": f"{OWNER}/{name}", "path": str(destination), "tag": tag(name)})
    return result


def main() -> int:
    global VERSION
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", default=VERSION,
                        help="module release version used for the initial tag "
                             "and for rewritten cross-module dependency tags")
    args = parser.parse_args()
    VERSION = args.version
    print(json.dumps({"repositories": export(args.output.absolute())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
