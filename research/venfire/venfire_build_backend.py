"""Release-guarded PEP 517 backend for the standalone VenFire package.

The guard runs before setuptools is imported for a build operation. A copied
developer tree, stale developer staging profile, symlinked profile, or marker
file therefore cannot be relabelled as a normal wheel or source archive.
"""

from __future__ import annotations

import ast
from pathlib import Path
import stat


PROFILE = Path("venfire/_build_profile.py")


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _literal_release_profile(path: Path) -> None:
    if _is_link(path) or not path.is_file():
        raise RuntimeError("Release profile must be a regular, non-symlink file")
    try:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise RuntimeError("Release profile is not valid source") from exc
    nodes = list(module.body)
    if (nodes and isinstance(nodes[0], ast.Expr)
            and isinstance(nodes[0].value, ast.Constant)
            and type(nodes[0].value.value) is str):
        nodes.pop(0)
    assignments = []
    for node in nodes:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            raise RuntimeError("Release profile may contain only one literal assignment")
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != "BUILD_PROFILE":
            raise RuntimeError("Release profile must assign BUILD_PROFILE")
        if not isinstance(node.value, ast.Constant) or type(node.value.value) is not str:
            raise RuntimeError("BUILD_PROFILE must be a literal string")
        assignments.append(node.value.value)
    if assignments == ["developer-nonredistributable"]:
        raise RuntimeError("NONREDISTRIBUTABLE developer build cannot be packaged as release")
    if assignments != ["release"]:
        raise RuntimeError("A release build requires exactly BUILD_PROFILE = 'release'")


def _iter_named(root: Path, name: str):
    # rglob includes dangling symlinks on the supported POSIX hosts. The direct
    # root check below also covers platforms whose glob implementation omits
    # them.
    direct = root / name
    if direct.exists() or direct.is_symlink():
        yield direct
    for path in root.rglob(name):
        if path != direct:
            yield path


def check_release_tree(root: str | Path | None = None) -> dict:
    """Validate a source or staging tree without executing project code."""

    base = Path(root or Path.cwd())
    if _is_link(base) or not base.is_dir():
        raise RuntimeError("Release tree must be a real directory")
    base = base.resolve()
    _literal_release_profile(base / PROFILE)
    markers = list(_iter_named(base, "DEVELOPMENT_ONLY.json"))
    if markers:
        raise RuntimeError("NONREDISTRIBUTABLE developer marker is present")
    # PEP 517 backends may be called after a prior build left build/lib or a
    # wheel staging directory behind. Every copied profile must still be the
    # literal release profile.
    for profile in _iter_named(base, "_build_profile.py"):
        if profile != (base / PROFILE).resolve():
            _literal_release_profile(profile)
    return {"root": str(base), "build_profile": "release"}


def _build_meta():
    from setuptools import build_meta

    return build_meta


def get_requires_for_build_wheel(config_settings=None):
    return _build_meta().get_requires_for_build_wheel(config_settings)


def get_requires_for_build_sdist(config_settings=None):
    return _build_meta().get_requires_for_build_sdist(config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    check_release_tree()
    return _build_meta().prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    check_release_tree()
    return _build_meta().build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    check_release_tree()
    return _build_meta().build_sdist(sdist_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    check_release_tree()
    return _build_meta().build_editable(wheel_directory, config_settings, metadata_directory)
