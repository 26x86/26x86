"""Shared package ownership for the seven independently versioned Git modules."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True)
class PackageOwner:
    module: str
    manifest: str = "Cargo.toml"

    @property
    def primary(self) -> str:
        return "nextcore-" + self.module.lower()

    @property
    def url(self) -> str:
        return f"https://github.com/26x86/Nextcore-{self.module}.git"

    @property
    def module_path(self) -> Path:
        return Path("nextcore/crates") / self.primary


# An auxiliary package is not another repository or workspace member.
PACKAGES = {
    "nextcore-core": PackageOwner("Core"),
    "nextcore-efi": PackageOwner("EFI"),
    "nextcore-tool": PackageOwner("Tool"),
    "nextcore-ise": PackageOwner("ISE"),
    "nextcore-gpu": PackageOwner("GPU"),
    "nextcore-hal": PackageOwner("HAL"),
    "nextcore-apls": PackageOwner("APLS"),
    "nextcore-memory-service": PackageOwner("ISE", "runtime/memory-service/Cargo.toml"),
}
PRIMARY_PACKAGES = {name: owner for name, owner in PACKAGES.items() if name == owner.primary}
DEPENDENCY_SECTIONS = ("dependencies", "build-dependencies", "dev-dependencies")
MEMORY_FEATURE = "nextcore-efi/arm-jit-memory-provider"


def is_nextcore(name: object) -> bool:
    return isinstance(name, str) and name.lower().startswith("nextcore-")


def dependency_tables(manifest: dict):
    for section in DEPENDENCY_SECTIONS:
        yield section, manifest.get(section, {})
    for target, tables in manifest.get("target", {}).items():
        for section in DEPENDENCY_SECTIONS:
            yield f"target.{target}.{section}", tables.get(section, {})
    yield "workspace.dependencies", manifest.get("workspace", {}).get("dependencies", {})


def merge_revisions(destination: dict[str, str], additions: dict[str, str]) -> None:
    for url, revision in additions.items():
        if url in destination and destination[url] != revision:
            raise ValueError(f"{url}: conflicting immutable dependency revisions")
        destination[url] = revision


def dependency_revisions(manifest: dict, heads: dict[str, str] | None = None) -> dict[str, str]:
    """Validate package names (including aliases) and collect one revision per owner."""
    revisions: dict[str, str] = {}
    inherited = manifest.get("workspace", {}).get("dependencies", {})
    for location, dependencies in dependency_tables(manifest):
        for alias, specification in dependencies.items():
            if isinstance(specification, dict) and specification.get("workspace") is True:
                # Independent modules may use their own workspace declaration;
                # they cannot silently inherit an unvalidated parent revision.
                base = inherited.get(alias)
                if isinstance(base, str):
                    base = {"version": base}
                if not isinstance(base, dict) or base.get("workspace"):
                    raise ValueError(f"{location}.{alias}: independent package has an unresolved workspace dependency")
                specification = {**base, **{k: v for k, v in specification.items() if k != "workspace"}}
            package = specification.get("package", alias) if isinstance(specification, dict) else alias
            if not is_nextcore(alias) and not is_nextcore(package):
                continue
            if not isinstance(package, str) or package not in PACKAGES or (is_nextcore(alias) and alias != package):
                raise ValueError(f"{location}.{alias}: unknown or conflicting Nextcore package {package}")
            owner = PACKAGES[package]
            if (not isinstance(specification, dict)
                    or any(key in specification for key in ("path", "branch", "tag", "workspace"))
                    or specification.get("git") != owner.url
                    or not isinstance(specification.get("rev"), str)
                    or not re.fullmatch(r"[0-9a-f]{40}", specification.get("rev", ""))):
                raise ValueError(f"{location}.{alias}: {package} must pin its canonical owner URL and immutable rev")
            revision = specification["rev"]
            if heads is not None and revision != heads[owner.primary]:
                raise ValueError(f"{location}.{alias}: {package} must pin the integrated remote revision")
            merge_revisions(revisions, {owner.url.removesuffix(".git"): revision})
    return revisions


@dataclass
class ModulePackages:
    manifests: dict[str, dict]
    dependency_revisions: dict[str, str]


def module_manifests(root: Path, primary: str, paths: list[str],
                     heads: dict[str, str] | None = None) -> ModulePackages:
    """Read tracked/public manifests, rejecting auxiliary copies in other owners or paths."""
    found = {}
    revisions: dict[str, str] = {}
    for relative in paths:
        path = Path(relative)
        if path.name != "Cargo.toml":
            continue
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{primary}: invalid manifest path {relative}")
        absolute = root / path
        if not absolute.is_file() or absolute.is_symlink() or not absolute.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"{primary}: manifest must be an ordinary owned file: {relative}")
        manifest = tomllib.loads(absolute.read_text())
        merge_revisions(revisions, dependency_revisions(manifest, heads))
        name = manifest.get("package", {}).get("name", "")
        if not is_nextcore(name):
            continue
        owner = PACKAGES.get(name)
        if owner is None or owner.primary != primary or path.as_posix() != owner.manifest:
            raise ValueError(f"{primary}: unknown package or wrong owner/path for {name}")
        if name in found:
            raise ValueError(f"{primary}: duplicate owned package {name}")
        found[name] = manifest
    required = {name for name, owner in PACKAGES.items() if owner.primary == primary}
    if set(found) != required:
        raise ValueError(f"{primary}: missing owned package manifests: {sorted(required - set(found))}")
    return ModulePackages(found, revisions)


def validate_auxiliary_inventory(root: Path, primary: str, tracked: set[str], inventory: dict) -> None:
    """The auxiliary source remains covered by its owner's existing file inventory."""
    import hashlib

    items = {item["path"]: item for item in inventory["files"]}
    if len(items) != len(inventory["files"]):
        raise ValueError(f"{primary}: duplicate inventory paths")
    for name, owner in PACKAGES.items():
        if owner.primary != primary or name == primary:
            continue
        prefix = Path(owner.manifest).parent.as_posix() + "/"
        expected = {path for path in tracked if path.startswith(prefix)}
        selected = {path for path in items if path.startswith(prefix)}
        if owner.manifest not in expected or selected != expected:
            raise ValueError(f"{name}: owner inventory must cover the tracked auxiliary files exactly")
        for relative in selected:
            path = root / relative
            if (not path.is_file() or path.is_symlink()
                    or not path.resolve().is_relative_to(root.resolve())):
                raise ValueError(f"{name}: auxiliary inventory path is not an ordinary owned file")
            data = path.read_bytes()
            if len(data) != items[relative]["bytes"] or hashlib.sha256(data).hexdigest() != items[relative]["sha256"]:
                raise ValueError(f"{name}: stale owner inventory for {relative}")


def validate_workspace(root: Path, manifest: dict) -> None:
    expected_members = {owner.module_path.relative_to("nextcore").as_posix() for owner in PRIMARY_PACKAGES.values()}
    members = manifest.get("workspace", {}).get("members", [])
    if len(members) != len(expected_members) or set(members) != expected_members:
        raise ValueError("Cargo workspace must declare exactly the seven primary module members")
    found = set()
    for url, entries in manifest.get("patch", {}).items():
        for alias, specification in entries.items():
            package = specification.get("package", alias) if isinstance(specification, dict) else alias
            if not is_nextcore(alias) and not is_nextcore(package):
                continue
            owner = PACKAGES.get(package) if isinstance(package, str) else None
            if owner is None or alias != package or url != owner.url or not isinstance(specification, dict):
                raise ValueError(f"{alias}: workspace patch has an unknown package or wrong owner URL")
            if set(specification) != {"path"} or not isinstance(specification["path"], str):
                raise ValueError(f"{package}: workspace patch requires only an explicit local path")
            expected = root / owner.module_path / Path(owner.manifest).parent
            selected = root / "nextcore" / specification["path"]
            if selected.resolve() != expected.resolve() or package in found:
                raise ValueError(f"{package}: workspace patch must select its unique local owner path")
            found.add(package)
    if found != set(PACKAGES):
        raise ValueError(f"Cargo workspace is missing owned package patches: {sorted(set(PACKAGES) - found)}")


def validate_cargo_metadata(root: Path, metadata: dict) -> dict:
    """Check actual feature-enabled Cargo packages, membership and dependency edges."""
    packages = [package for package in metadata["packages"] if is_nextcore(package["name"])]
    if len(packages) != len(PACKAGES) or {p["name"] for p in packages} != set(PACKAGES):
        raise ValueError("Cargo resolved unknown, missing or duplicate Nextcore packages")
    members = set(metadata["workspace_members"])
    by_name = {package["name"]: package for package in packages}
    expected_members = {by_name[name]["id"] for name in PRIMARY_PACKAGES}
    if members != expected_members or len(metadata["workspace_members"]) != len(expected_members):
        raise ValueError("Cargo must resolve exactly seven primary workspace members; auxiliary is not a member")
    for name, package in by_name.items():
        owner = PACKAGES[name]
        expected = root / owner.module_path / owner.manifest
        if Path(package["manifest_path"]).resolve() != expected.resolve() or package["source"] is not None:
            raise ValueError(f"{name}: Cargo did not resolve its local submodule owner")
    nodes = {node["id"]: node for node in (metadata.get("resolve") or {}).get("nodes", [])}
    efi = by_name["nextcore-efi"]["id"]
    if efi not in nodes or "arm-jit-memory-provider" not in nodes[efi].get("features", []):
        raise ValueError("Cargo metadata must enable the EFI memory-provider feature")
    visited, pending = set(), [efi]
    while pending:
        package_id = pending.pop()
        if package_id in visited:
            continue
        visited.add(package_id)
        if package_id not in nodes:
            raise ValueError("Cargo dependency graph is missing a selected package node")
        pending.extend(nodes[package_id].get("dependencies", []))
    if by_name["nextcore-memory-service"]["id"] not in visited:
        raise ValueError("Cargo memory service is not selected by the EFI dependency graph")
    return {"workspace_members": len(members), "owned_packages": len(packages),
            "memory_service_local_and_selected": True}
