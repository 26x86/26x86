"""Immutable local input manifests: describe and verify, never patch or copy.

SHA-256 establishes byte identity, not provenance, licensing, signature validity,
or bootability. All source access is read-only and restricted to regular files.
The caller should verify immediately before and after any consuming operation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator


_SCHEMA_VERSION = 1
_CHUNK_BYTES = 1024 * 1024
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_KIND = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


class ArtifactInputError(ValueError):
    """Input is not a safe, stable local regular file."""


class ArtifactChangedError(ArtifactInputError):
    """Input metadata or identity changed during a read."""


class ManifestError(ValueError):
    """Manifest schema or destination is invalid."""


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    size_bytes: int
    sha256: str
    kind: str = "input"

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "size_bytes": self.size_bytes, "sha256": self.sha256, "kind": self.kind}


@dataclass(frozen=True)
class ArtifactManifest:
    artifacts: tuple[ArtifactRecord, ...]
    created_at: str
    schema_version: int = _SCHEMA_VERSION
    algorithm: str = "sha256"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "artifacts": [entry.to_dict() for entry in self.artifacts],
        }


@dataclass(frozen=True)
class VerificationIssue:
    path: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class VerificationReport:
    checked_count: int
    issues: tuple[VerificationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "checked_count": self.checked_count, "issues": [item.to_dict() for item in self.issues]}


class ArtifactIntegrityError(RuntimeError):
    def __init__(self, report: VerificationReport):
        self.report = report
        super().__init__("Input integrity verification failed: " + "; ".join(f"{item.path}: {item.reason}" for item in report.issues))


def _absolute_path(path: str | os.PathLike[str]) -> Path:
    try:
        raw = os.fspath(path)
        if not isinstance(raw, str) or not raw or "\x00" in raw:
            raise ArtifactInputError("A nonempty filesystem path is required")
        if ".." in Path(raw).parts:
            raise ArtifactInputError("Parent traversal components are forbidden; pass a direct path")
        absolute = Path(os.path.abspath(raw))
    except (TypeError, OSError, ValueError) as exc:
        raise ArtifactInputError("Invalid filesystem path") from exc
    # UNC/device namespaces can address remote shares and raw devices on Windows.
    if os.name == "nt" and (str(absolute).startswith("\\\\") or ":" in str(absolute)[2:]):
        raise ArtifactInputError("UNC, device namespace, and alternate-stream paths are forbidden")
    return absolute


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _inspect_path(path: Path, *, must_exist: bool = True) -> os.stat_result | None:
    """Reject links/junctions at every component, before resolving any target."""
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            if component == path and not must_exist:
                return None
            raise
        if _is_link(info):
            raise ArtifactInputError("Symlink or reparse-point paths are forbidden")
        if component != path and not stat.S_ISDIR(info.st_mode):
            raise ArtifactInputError("A path parent is not a directory")
    return info


def _identity(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _open_fd(path: Path, flags: int, mode: int = 0o600) -> int:
    """On Darwin/POSIX pin each directory component with O_NOFOLLOW.

    Windows development diagnostics additionally reject all reparse points via
    lstat and compare file identity before reading; they do not run Apple guests.
    """
    if os.name != "posix" or os.open not in os.supports_dir_fd:
        return os.open(path, flags, mode)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(path.anchor, directory_flags)
    try:
        for component in path.parts[1:-1]:
            child_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd
        return os.open(path.name, flags | os.O_NOFOLLOW, mode, dir_fd=directory_fd)
    finally:
        os.close(directory_fd)


def _open_regular(path: Path) -> tuple[BinaryIO, os.stat_result]:
    before = _inspect_path(path)
    if before is None or not stat.S_ISREG(before.st_mode):
        raise ArtifactInputError("Only regular files are accepted (no devices, directories, or pipes)")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = _open_fd(path, flags)
    try:
        opened = os.fstat(fd)
        current = _inspect_path(path)
        if current is None or not stat.S_ISREG(opened.st_mode) or _identity(before) != _identity(opened) or _identity(current) != _identity(opened):
            raise ArtifactChangedError("File identity changed while opening input")
        stream = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    return stream, opened


def _finish_read(path: Path, stream: BinaryIO, before: os.stat_result) -> None:
    after = os.fstat(stream.fileno())
    current = _inspect_path(path)
    if current is None or _identity(before) != _identity(after) or _identity(after) != _identity(current):
        raise ArtifactChangedError("File identity or metadata changed during input read")


@contextmanager
def read_regular(path: str | os.PathLike[str]) -> Iterator[BinaryIO]:
    """Yield a read-only binary stream; verify stable identity even on errors.

    The consumer may seek/read, but must not close this borrowed stream. This
    detects concurrent file/metadata changes, not authenticity or byte identity
    against a previously saved SHA-256 manifest.
    """
    absolute = _absolute_path(path)
    stream, before = _open_regular(absolute)
    with stream:
        try:
            yield stream
        finally:
            _finish_read(absolute, stream, before)


def hash_artifact(path: str | os.PathLike[str], *, kind: str = "input") -> ArtifactRecord:
    if not isinstance(kind, str) or _KIND.fullmatch(kind) is None:
        raise ArtifactInputError("Artifact kind must be a lowercase identifier")
    absolute = _absolute_path(path)
    stream, before = _open_regular(absolute)
    digest = hashlib.sha256()
    count = 0
    with stream:
        while True:
            chunk = stream.read(_CHUNK_BYTES)
            if not chunk:
                break
            count += len(chunk)
            digest.update(chunk)
        _finish_read(absolute, stream, before)
    if count != before.st_size:
        raise ArtifactChangedError("Read length changed during input read")
    return ArtifactRecord(str(absolute), count, digest.hexdigest(), kind)


def create_manifest(paths: Iterable[str | os.PathLike[str]], *, kind: str = "input") -> ArtifactManifest:
    if isinstance(paths, (str, bytes, os.PathLike)):
        raise ArtifactInputError("Pass an iterable of paths, not a single path")
    records: list[ArtifactRecord] = []
    seen: set[str] = set()
    for path in paths:
        record = hash_artifact(path, kind=kind)
        key = os.path.normcase(record.path)
        if key in seen:
            raise ArtifactInputError("Duplicate artifact path")
        seen.add(key)
        records.append(record)
    if not records:
        raise ArtifactInputError("At least one artifact is required")
    return ArtifactManifest(tuple(records), datetime.now(timezone.utc).isoformat())


def _parse_manifest(data: Any) -> ArtifactManifest:
    if not isinstance(data, dict) or set(data) != {"schema_version", "algorithm", "created_at", "artifacts"}:
        raise ManifestError("Invalid manifest fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != _SCHEMA_VERSION or data["algorithm"] != "sha256":
        raise ManifestError("Unsupported manifest schema or hash algorithm")
    created_at = data["created_at"]
    try:
        if not isinstance(created_at, str) or datetime.fromisoformat(created_at).utcoffset() is None:
            raise ValueError("Missing timezone")
    except (ValueError, TypeError) as exc:
        raise ManifestError("Invalid manifest creation timestamp") from exc
    raw_records = data["artifacts"]
    if not isinstance(raw_records, list) or not raw_records:
        raise ManifestError("Manifest must contain artifact records")
    records: list[ArtifactRecord] = []
    seen: set[str] = set()
    for raw in raw_records:
        if not isinstance(raw, dict) or set(raw) != {"path", "size_bytes", "sha256", "kind"}:
            raise ManifestError("Invalid artifact fields")
        path, size, digest, kind = raw["path"], raw["size_bytes"], raw["sha256"], raw["kind"]
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ManifestError("Artifact paths must be absolute")
        try:
            absolute = str(_absolute_path(path))
        except ArtifactInputError as exc:
            raise ManifestError(str(exc)) from exc
        if absolute != path:
            raise ManifestError("Artifact paths must be normalized absolute paths")
        if type(size) is not int or size < 0 or not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ManifestError("Invalid artifact byte length or SHA-256")
        if not isinstance(kind, str) or _KIND.fullmatch(kind) is None:
            raise ManifestError("Invalid artifact kind")
        key = os.path.normcase(path)
        if key in seen:
            raise ManifestError("Duplicate artifact path")
        seen.add(key)
        records.append(ArtifactRecord(path, size, digest, kind))
    return ArtifactManifest(tuple(records), created_at)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError("Duplicate JSON key in manifest")
        result[key] = value
    return result


def load_manifest(path: str | os.PathLike[str]) -> ArtifactManifest:
    absolute = _absolute_path(path)
    stream, before = _open_regular(absolute)
    with stream:
        if before.st_size > _MAX_MANIFEST_BYTES:
            raise ManifestError("Manifest exceeds size limit")
        encoded = stream.read(_MAX_MANIFEST_BYTES + 1)
        _finish_read(absolute, stream, before)
    if len(encoded) > _MAX_MANIFEST_BYTES:
        raise ManifestError("Manifest exceeds size limit")
    try:
        data = json.loads(encoded, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise ManifestError("Invalid manifest JSON") from exc
    return _parse_manifest(data)


def write_manifest(manifest: ArtifactManifest, path: str | os.PathLike[str]) -> Path:
    """Create a new manifest exclusively; never overwrite any existing file."""
    checked = _parse_manifest(manifest.to_dict())
    absolute = _absolute_path(path)
    if os.path.normcase(str(absolute)) in {os.path.normcase(record.path) for record in checked.artifacts}:
        raise ManifestError("Manifest destination cannot be a source artifact")
    _inspect_path(absolute, must_exist=False)
    encoded = (json.dumps(checked.to_dict(), indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    if len(encoded) > _MAX_MANIFEST_BYTES:
        raise ManifestError("Manifest exceeds size limit")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = _open_fd(absolute, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return absolute


def verify_manifest(manifest: ArtifactManifest) -> VerificationReport:
    checked = _parse_manifest(manifest.to_dict())
    issues: list[VerificationIssue] = []
    for expected in checked.artifacts:
        try:
            actual = hash_artifact(expected.path, kind=expected.kind)
            if actual.size_bytes != expected.size_bytes:
                issues.append(VerificationIssue(expected.path, "byte length differs from manifest"))
            elif actual.sha256 != expected.sha256:
                issues.append(VerificationIssue(expected.path, "SHA-256 differs from manifest"))
        except (OSError, ArtifactInputError) as exc:
            # Include a useful stable error without arbitrary OS/tool output.
            reason = str(exc) if isinstance(exc, ArtifactInputError) else type(exc).__name__
            issues.append(VerificationIssue(expected.path, reason))
    return VerificationReport(len(checked.artifacts), tuple(issues))


def require_intact(manifest: ArtifactManifest) -> VerificationReport:
    report = verify_manifest(manifest)
    if not report.valid:
        raise ArtifactIntegrityError(report)
    return report
