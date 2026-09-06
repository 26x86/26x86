"""Persistent guest writes over immutable raw inputs, never a base-image commit.

Only the guest's normal disk writes enter qcow2 overlays. Neither signatures nor
guest code are changed here. Both VMApple block interfaces share the same state.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import struct
import subprocess

from .artifacts import (_absolute_path, _inspect_path, ArtifactManifest, create_manifest,
                        load_manifest, read_regular, require_intact, write_manifest)


@dataclass(frozen=True)
class StorageSession:
    directory: Path
    manifest: ArtifactManifest
    aux_offset: int

    def validate(self):
        require_intact(self.manifest)
        if len(self.manifest.artifacts) != 2:
            raise ValueError("A storage session requires exactly AUX and root base images")
        _sizes(self.manifest, self.aux_offset)
        for role, size in zip(("aux", "root"), _sizes(self.manifest, self.aux_offset)):
            _check_overlay(self.directory / (role + ".qcow2"), size)

    def arguments(self, *, allow_bdif_writes=False) -> list[str]:
        """Explicit file/raw/qcow2 graph: never follow an embedded backing path."""
        if type(allow_bdif_writes) is not bool:
            raise ValueError("allow_bdif_writes must be an explicit boolean")
        self.validate()
        arguments = []
        if allow_bdif_writes:
            arguments.extend(["-global", "vmapple-bdif.allow-block-writes=on"])
        for index, (role, base) in enumerate(zip(("aux", "root"), self.manifest.artifacts)):
            node_name = "venfire_" + role
            offset = self.aux_offset if index == 0 else 0
            backing = {"driver": "raw", "read-only": True, "offset": offset,
                       "file": {"driver": "file", "filename": base.path, "read-only": True}}
            node = {"driver": "qcow2", "node-name": node_name, "read-only": False,
                    "file": {"driver": "file", "filename": str(self.directory / (role + ".qcow2"))},
                    "backing": backing}
            arguments.extend(["-blockdev", json.dumps(node, separators=(",", ":"))])
            view = "json:" + json.dumps({"driver": "raw", "file": node_name}, separators=(",", ":"))
            escaped = view.replace(",", ",,")
            flash_readonly = "off" if allow_bdif_writes else "on"
            shared_writer = ",share-rw=on" if allow_bdif_writes else ""
            arguments.extend(["-drive", f"if=pflash,index={index},readonly={flash_readonly},file={escaped}",
                              "-drive", f"if=none,id={role}disk,werror=report,rerror=report,cache=writeback,file={escaped}",
                              "-device", f"vmapple-virtio-blk-pci,variant={role},drive={role}disk{shared_writer}"])
        return arguments


def _sizes(manifest, aux_offset):
    if type(aux_offset) is not int or aux_offset < 0 or aux_offset % 512:
        raise ValueError("AUX offset must be a nonnegative multiple of 512")
    if len(manifest.artifacts) != 2:
        raise ValueError("A storage session requires exactly AUX and root base images")
    sizes = [manifest.artifacts[0].size_bytes - aux_offset, manifest.artifacts[1].size_bytes]
    if any(size <= 0 or size % 512 for size in sizes):
        raise ValueError("AUX view and root must be nonempty multiples of 512 bytes")
    return sizes


def _check_overlay(path, expected_size):
    # Header layout: QEMU docs/interop/qcow2.rst. Refuse external data, encrypted
    # images and on-disk backing names before QEMU can resolve additional paths.
    with read_regular(path) as source:
        header = source.read(104)
    if len(header) != 104 or header[:4] != b"QFI\xfb":
        raise ValueError("Invalid qcow2 overlay header")
    version, backing_offset, backing_size = struct.unpack_from(">IQI", header, 4)
    virtual_size, crypt = struct.unpack_from(">QI", header, 24)
    incompatible = struct.unpack_from(">Q", header, 72)[0]
    if (version != 3 or backing_offset or backing_size or virtual_size != expected_size
            or crypt or incompatible & ~1):
        raise ValueError("Overlay must be qcow2 v3, expected size, unencrypted, without external paths/features")


def prepare_storage(*, aux, disk, directory, qemu_img="qemu-img", aux_offset=0):
    manifest = create_manifest([aux, disk])
    sizes = _sizes(manifest, aux_offset)
    executable = shutil.which(qemu_img)
    if executable is None:
        raise ValueError("qemu-img not found")
    tool_manifest = create_manifest([executable])
    executable = tool_manifest.artifacts[0].path
    destination = _absolute_path(directory)
    _inspect_path(destination, must_exist=False)
    destination.mkdir(exist_ok=False)
    write_manifest(manifest, destination / "bases.json")
    write_manifest(tool_manifest, destination / "creation-tool.json")
    for role, size in zip(("aux", "root"), sizes):
        require_intact(tool_manifest)
        subprocess.run([executable, "create", "-f", "qcow2", "-o", "compat=1.1,lazy_refcounts=off",
                        str(destination / (role + ".qcow2")), str(size)],
                       check=True, capture_output=True, text=True, timeout=30)
    require_intact(tool_manifest)
    session = StorageSession(destination, manifest, aux_offset)
    session.validate()
    with (destination / "session.json").open("x", encoding="utf-8") as output:
        json.dump({"schema": 1, "aux_offset": aux_offset,
                   "base_images_read_only": True, "writes": "separate qcow2 overlays",
                   "backing_paths": "supplied explicitly from bases.json by 26x86",
                   "macos_boot_verified": False}, output, indent=2)
        output.write("\n")
    return session


def load_storage(directory):
    directory = _absolute_path(directory)
    with read_regular(directory / "session.json") as source:
        data = source.read(16385)
    if len(data) > 16384:
        raise ValueError("Storage session metadata exceeds limit")
    metadata = json.loads(data)
    if not isinstance(metadata, dict) or metadata.get("schema") != 1:
        raise ValueError("Unknown storage session schema")
    session = StorageSession(directory, load_manifest(directory / "bases.json"), metadata.get("aux_offset"))
    session.validate()
    return session
