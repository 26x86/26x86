"""Journaled Mellow data-volume backup/readback/restore, without APFS or kext operations.

Native host/security authorization belongs to the caller. Tests use an explicit
temporary data_root. Receipts are integrity checks in an owner-controlled journal,
not signatures against an attacker who already has root access. Concurrent kernel
or third-party writes are not silently overwritten during restoration.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import uuid

from .payload import DESTINATIONS, ValidatedPayload, load_payload


DEFAULT_JOURNAL = "/Library/Application Support/26x86/Mellow/transaction"
STATES = {"preparing", "prepared", "files_verified", "rollback_pending", "restored"}


class TransactionError(ValueError):
    """A transaction is incomplete, inconsistent, or would escape its allowed files."""


def _reject_link(path: Path) -> None:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise TransactionError("Symlink/reparse point rejected: " + str(path))


def _checked_path(path: Path) -> Path:
    path = path.absolute()
    for part in reversed((path, *path.parents)):
        if part.exists() or part.is_symlink():
            _reject_link(part)
    return path.resolve(strict=False)


def _roots(data_root, journal_root):
    data = _checked_path(Path(data_root))
    if not data.is_dir():
        raise TransactionError("Data root must be an existing directory")
    journal = _checked_path(Path(journal_root) if journal_root is not None else data / DEFAULT_JOURNAL.lstrip("/"))
    if journal == data or journal in data.parents:
        raise TransactionError("Journal must not contain the data root")
    for destination in DESTINATIONS.values():
        target = data / destination.lstrip("/")
        if journal == target or target in journal.parents or journal in target.parents:
            raise TransactionError("Journal overlaps a component destination")
    return data, journal


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "\x00" in value:
        raise TransactionError("Invalid receipt relative path")
    if value == ".":
        return value
    if PurePosixPath(value).is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise TransactionError("Receipt path traversal rejected")
    return value


def _tree(path: Path):
    _checked_path(path)
    if not path.exists():
        return None
    if not path.is_dir():
        raise TransactionError("Expected a component directory: " + str(path))
    records = {}
    paths = [path]
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            child = Path(base) / name
            _reject_link(child)
            paths.append(child)
    for item in sorted(paths):
        relative = "." if item == path else _relative(item.relative_to(path).as_posix())
        info = item.lstat()
        record = {"mode": stat.S_IMODE(info.st_mode), "uid": getattr(info, "st_uid", None),
                  "gid": getattr(info, "st_gid", None)}
        if stat.S_ISDIR(info.st_mode):
            record["kind"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            data = item.read_bytes()
            record.update(kind="file", size=len(data), sha256=hashlib.sha256(data).hexdigest())
        else:
            raise TransactionError("Non-regular component entry")
        records[relative] = record
    return records


def _signature(tree, *, metadata=False, ownership=False):
    if tree is None:
        return None
    keys = ("kind", "size", "sha256", "mode") if metadata else ("kind", "size", "sha256")
    if ownership:
        keys += ("uid", "gid")
    return {name: {k: record[k] for k in keys if k in record} for name, record in tree.items()}


def _validate_tree_record(tree, *, required):
    if tree is None and not required:
        return
    if not isinstance(tree, dict) or "." not in tree or len(tree) > 10000:
        raise TransactionError("Invalid receipt tree inventory")
    for name, record in tree.items():
        _relative(name)
        if not isinstance(record, dict) or record.get("kind") not in {"file", "directory"}:
            raise TransactionError("Invalid receipt tree entry")
        keys = {"mode", "uid", "gid", "kind"}
        if record["kind"] == "file":
            keys |= {"size", "sha256"}
            if type(record.get("size")) is not int or record["size"] < 0 or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256", ""))):
                raise TransactionError("Invalid receipt file digest/size")
        if set(record) != keys or type(record["mode"]) is not int or not 0 <= record["mode"] <= 0o7777:
            raise TransactionError("Invalid receipt file metadata")
        if any(v is not None and (type(v) is not int or v < 0) for v in (record["uid"], record["gid"])):
            raise TransactionError("Invalid receipt owner metadata")
        if name == "." and record["kind"] != "directory":
            raise TransactionError("Receipt root is not a directory")
        if name != ".":
            parent = PurePosixPath(name).parent.as_posix()
            if parent not in tree or tree[parent].get("kind") != "directory":
                raise TransactionError("Receipt entry has no parent directory")


def _canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sync_directory(path):
    if os.name == "posix":
        handle = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(handle)
        finally:
            os.close(handle)


def _sync_tree(path):
    if not path.exists():
        return
    directories = [path]
    for base, dirs, files in os.walk(path, followlinks=False):
        directories += [Path(base) / name for name in dirs]
        for name in files:
            file = Path(base) / name
            if os.name == "nt":
                # Windows CRT _commit requires a writable handle. Preserve the
                # original read-only attribute around the flush of our snapshot.
                mode = stat.S_IMODE(file.stat().st_mode)
                os.chmod(file, mode | stat.S_IWRITE)
                try:
                    with file.open("r+b") as handle:
                        os.fsync(handle.fileno())
                finally:
                    os.chmod(file, mode)
            else:
                with file.open("rb") as handle:
                    os.fsync(handle.fileno())
    for directory in reversed(directories):
        _sync_directory(directory)


def _write_receipt(active, record):
    _checked_path(active)
    receipt = _checked_path(active / "receipt.json")
    envelope = {"record": record, "sha256": hashlib.sha256(_canonical(record)).hexdigest()}
    temporary = active / ("receipt-" + uuid.uuid4().hex + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(envelope, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, receipt)
    _sync_directory(active)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TransactionError("Duplicate receipt JSON key")
        result[key] = value
    return result


def _load_receipt(data, journal):
    active = _checked_path(journal / "active")
    path = _checked_path(active / "receipt.json")
    if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise TransactionError("Pending/incomplete transaction receipt; do not start a new write")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (ValueError, OSError) as error:
        raise TransactionError("Unreadable transaction receipt") from error
    if not isinstance(envelope, dict) or set(envelope) != {"record", "sha256"}:
        raise TransactionError("Invalid receipt envelope")
    record = envelope["record"]
    if not isinstance(record, dict) or hashlib.sha256(_canonical(record)).hexdigest() != envelope["sha256"]:
        raise TransactionError("Receipt integrity mismatch")
    if set(record) != {"schema_version", "transaction_id", "data_root", "source_commit", "state", "components"}:
        raise TransactionError("Unexpected receipt fields")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1 or record["data_root"] != str(data):
        raise TransactionError("Receipt schema or data root differs")
    if not re.fullmatch(r"[0-9a-f]{32}", str(record["transaction_id"])) or not re.fullmatch(r"[0-9a-f]{40}", str(record["source_commit"])):
        raise TransactionError("Invalid receipt identifiers")
    if record["state"] not in STATES or not isinstance(record["components"], list) or not 1 <= len(record["components"]) <= 3:
        raise TransactionError("Invalid receipt state/components")
    categories = set()
    for component in record["components"]:
        if not isinstance(component, dict) or set(component) != {"category", "destination", "original", "expected"}:
            raise TransactionError("Invalid receipt component")
        category = component["category"]
        if not isinstance(category, str) or category not in DESTINATIONS or category in categories or component["destination"] != DESTINATIONS[category]:
            raise TransactionError("Receipt destination is not an allowed Mellow component")
        categories.add(category)
        _validate_tree_record(component["original"], required=False)
        _validate_tree_record(component["expected"], required=True)
    return record


def _assert_snapshots(active, record):
    for component in record["components"]:
        category = component["category"]
        for name, tree in (("backups", component["original"]), ("expected", component["expected"])):
            actual = _tree(active / name / category)
            if _signature(actual, metadata=True) != _signature(tree, metadata=True):
                raise TransactionError("Journal snapshot changed or incomplete: " + category + "/" + name)


def _matches_partial(path, record, snapshot):
    if record["kind"] == "directory":
        return path.is_dir()
    current = path.read_bytes()
    if len(current) > record["size"]:
        return False
    # Only known complete bytes or a verified prefix from an interrupted copy.
    return snapshot.read_bytes()[:len(current)] == current


def _owned_current(data, active, component):
    target = _checked_path(data / DESTINATIONS[component["category"]].lstrip("/"))
    current = _tree(target)
    if current is None:
        return
    for name, item in current.items():
        allowed = False
        for group, tree in (("backups", component["original"]), ("expected", component["expected"])):
            if tree is None or name not in tree or tree[name]["kind"] != item["kind"]:
                continue
            snapshot = active / group / component["category"]
            candidate = target if name == "." else target / name
            original = snapshot if name == "." else snapshot / name
            if _matches_partial(candidate, tree[name], original):
                allowed = True
                break
        if not allowed:
            raise TransactionError("Target has third-party/unrecognized changes; refusing removal: " + str(target / name))


def _restore_metadata(path, tree):
    for name in sorted(tree, key=lambda n: len(PurePosixPath(n).parts), reverse=True):
        target = path if name == "." else path / name
        item = tree[name]
        if os.name == "posix" and item["uid"] is not None and item["gid"] is not None:
            os.chown(target, item["uid"], item["gid"])
        os.chmod(target, item["mode"])


def _assert_restored(data, record):
    for component in record["components"]:
        current = _tree(data / DESTINATIONS[component["category"]].lstrip("/"))
        if _signature(current, metadata=True, ownership=True) != _signature(component["original"], metadata=True, ownership=True):
            raise TransactionError("Restored target changed; cache/finalize retry will not overwrite it")


def _archive(data, journal, record):
    _assert_restored(data, record)
    history = _checked_path(journal / "history")
    history.mkdir(mode=0o700, exist_ok=True)
    archived = history / record["transaction_id"]
    if archived.exists() or archived.is_symlink():
        raise TransactionError("Completed transaction archive already exists")
    os.replace(journal / "active", archived)
    _sync_directory(history)
    _sync_directory(journal)
    return True


def _restore(data, journal, record, *, defer_finalize=False):
    active = journal / "active"
    if record["state"] == "preparing":
        raise TransactionError("Prepare did not complete; original targets were not authorized for overwrite")
    _assert_snapshots(active, record)
    if record["state"] == "restored":
        _assert_restored(data, record)
        return True if defer_finalize else _archive(data, journal, record)
    for component in record["components"]:
        _owned_current(data, active, component)
    record["state"] = "rollback_pending"
    _write_receipt(active, record)
    for component in reversed(record["components"]):
        target = _checked_path(data / DESTINATIONS[component["category"]].lstrip("/"))
        original = component["original"]
        current = _tree(target)
        if _signature(current, metadata=True, ownership=True) == _signature(original, metadata=True, ownership=True):
            if current is not None:
                _sync_tree(target)
            if target.parent.exists():
                _sync_directory(target.parent)
            continue
        if current is not None:
            # Exact allowlisted destination, no links, with every entry checked
            # against original/expected bytes. No receipt-supplied removal path.
            _owned_current(data, active, component)
            shutil.rmtree(target)
        if original is not None:
            _checked_path(target.parent)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(active / "backups" / component["category"], target)
            _restore_metadata(target, original)
        if _signature(_tree(target), metadata=True, ownership=True) != _signature(original, metadata=True, ownership=True):
            raise TransactionError("Restored target failed original hash/mode readback")
        if original is not None:
            _sync_tree(target)
        _sync_directory(target.parent)
    record["state"] = "restored"
    _write_receipt(active, record)
    return True if defer_finalize else _archive(data, journal, record)


class MellowTransaction:
    """One transaction; caller performs the actual file copy between the methods."""

    def __init__(self, payload: ValidatedPayload, data_root="/", journal_root=None):
        if not isinstance(payload, ValidatedPayload):
            raise TransactionError("Expected a validated Mellow payload")
        self.payload = payload
        self.data_root, self.journal_root = _roots(data_root, journal_root)
        if self.journal_root == payload.root or payload.root in self.journal_root.parents or self.journal_root in payload.root.parents:
            raise TransactionError("Journal overlaps payload source")
        self.transaction_id = None

    def prepare(self):
        active = _checked_path(self.journal_root / "active")
        if active.exists() or active.is_symlink():
            raise TransactionError("An active/pending Mellow transaction exists; a new write is forbidden")
        payload = load_payload(self.payload.root, mode="x86")
        components = []
        for component in payload.components:
            if component.category not in DESTINATIONS or component.destination != DESTINATIONS[component.category]:
                raise TransactionError("Component destination is not allowed")
            target = _checked_path(self.data_root / component.destination.lstrip("/"))
            if target == payload.root or target in payload.root.parents or payload.root in target.parents:
                raise TransactionError("Payload source overlaps target")
            original, expected = _tree(target), _tree(component.source)
            _validate_tree_record(expected, required=True)
            components.append(dict(category=component.category, destination=component.destination,
                                   original=original, expected=expected))
        missing = []
        ancestor = self.journal_root
        while not ancestor.exists():
            missing.append(ancestor)
            ancestor = ancestor.parent
        self.journal_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        _checked_path(self.journal_root)
        active.mkdir(mode=0o700)  # Atomic overlap exclusion: no exist_ok.
        self.transaction_id = uuid.uuid4().hex
        record = dict(schema_version=1, transaction_id=self.transaction_id, data_root=str(self.data_root),
                      source_commit=payload.source_commit, state="preparing", components=components)
        _write_receipt(active, record)
        for component in components:
            category = component["category"]
            if component["original"] is not None:
                shutil.copytree(self.data_root / component["destination"].lstrip("/"), active / "backups" / category)
            shutil.copytree(payload.root / ("root" + component["destination"]), active / "expected" / category)
        _assert_snapshots(active, record)
        _sync_tree(active / "backups")
        _sync_tree(active / "expected")
        # No destination has been written. A concurrent change invalidates prepare.
        for component in components:
            if _tree(self.data_root / component["destination"].lstrip("/")) != component["original"]:
                raise TransactionError("Original target changed during backup")
        payload.validate(mode="x86")
        record["state"] = "prepared"
        _write_receipt(active, record)
        _sync_directory(self.journal_root)
        for directory in missing:
            _sync_directory(directory.parent)
        return {"state": "prepared", "transaction_id": self.transaction_id, "data_volume_only": True}

    def installed(self):
        record = _load_receipt(self.data_root, self.journal_root)
        if record["transaction_id"] != self.transaction_id or record["state"] != "prepared":
            raise TransactionError("This instance has no prepared transaction")
        _assert_snapshots(self.journal_root / "active", record)
        for component in record["components"]:
            actual = _tree(self.data_root / DESTINATIONS[component["category"]].lstrip("/"))
            if _signature(actual) != _signature(component["expected"]):
                raise TransactionError("Installed component does not match verified payload bytes")
        record["state"] = "files_verified"
        _write_receipt(self.journal_root / "active", record)
        return {"state": "files_verified", "transaction_id": self.transaction_id,
                "kernel_cache_verified": False, "snapshot_verified": False, "native_loaded": False}

    def rollback(self):
        record = _load_receipt(self.data_root, self.journal_root)
        if self.transaction_id is None or record["transaction_id"] != self.transaction_id:
            raise TransactionError("This instance does not own the active transaction")
        return _restore(self.data_root, self.journal_root, record)


def restore_installed(data_root="/", journal_root=None, *, defer_finalize=False) -> bool:
    """Explicit unpatch/crash recovery. Return False for no active journal.

    A pending journal blocks new prepare calls but can be restored explicitly if
    its backups and target ownership checks pass. Errors leave the journal intact.
    defer_finalize keeps the restored receipt active for the caller's KC rebuild;
    after a successful cache rebuild, call finalize_restore to archive it.
    """
    data, journal = _roots(data_root, journal_root)
    active = _checked_path(journal / "active")
    if not active.exists():
        return False
    return _restore(data, journal, _load_receipt(data, journal), defer_finalize=defer_finalize)


def finalize_restore(data_root="/", journal_root=None) -> bool:
    """Archive a restored transaction only after the caller's cache step succeeds."""
    data, journal = _roots(data_root, journal_root)
    active = _checked_path(journal / "active")
    if not active.exists():
        return False
    record = _load_receipt(data, journal)
    if record["state"] != "restored":
        raise TransactionError("Cannot finalize a transaction before original files are restored")
    _assert_snapshots(active, record)
    return _archive(data, journal, record)
