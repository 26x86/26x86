"""VF-SPEC-001 §17 M0: strict XML configuration, never boot admission.

Original 26x86 implementation. The supplied document did not include reference
code. Schema decisions where v0.1 leaves spelling/bounds unspecified:

* Storage is 1..32 dictionaries with ID, Backend='raw-gpt-partition',
  DeviceSerial, DiskGUID, PartitionGUID, SectorBytes (512/4096), ReadOnly.
  Partition LBAs are measured at boot, never guessed from this configuration.
* Graphics.Device is 'auto' or a complete PCI selector dictionary: Segment,
  Bus, Device, Function, VendorID, DeviceID, SubsystemVendorID,
  SubsystemDeviceID, RevisionID. A selector is not a backend approval.
* CPU count/budget fields are bounded to 4096; memory uses positive MiB and
  overflow-safe uint64 byte limits. These parser bounds are not host capacity.
* Guest contains ProfileID and RequireMetal. The builtin conformance name is
  a structural M0 fixture, not an executable/image/adapter contract. macOS
  entries must come from a separate caller-supplied profile registry; config
  cannot supply its own approval or turn off required security.
* XML depth counts plist as level 1. Node count includes elements/comments.
  Only dict/array/key/string/integer/true/false are part of this schema;
  unsigned canonical decimal integers are accepted. XML whitespace is allowed
  around integers. Unknown keys and missing required keys are both errors.

Registry entry fields for macOS: Kind='macos', BuildID, ImageSHA256,
ABIVersion=1, MMUGranule (4096/16384), TimerFrequencyHz, BootABI='iBoot',
InterruptController='AIC', SoCContract, CPUFeatures (nonempty unique identifiers), GraphicsAdapter
(None or {ID,SHA256,SGPUABI=1,MetalValidated:bool}). These are declarations
bound by a later signed bundle, not facts verified by this offline parser.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any, Mapping
from xml.parsers import expat

MAX_BYTES = 1024 * 1024
MAX_DEPTH = 16
MAX_NODES = 4096
MAX_CPUS = 4096
MAX_MIB = ((1 << 64) - 1) // (1024 * 1024)
CONFORMANCE_PROFILE = "arm64-conformance-v1"
PLIST_PUBLIC_ID = "-//Apple//DTD PLIST 1.0//EN"
PLIST_SYSTEM_ID = "http://www.apple.com/DTDs/PropertyList-1.0.dtd"


class ConfigError(ValueError):
    """A deterministic fail-closed configuration error."""
    code = "E_CONFIG"


def _fail(message: str):
    raise ConfigError(message)


def parse_xml(data: bytes) -> dict[str, Any]:
    """Parse bounded UTF-8 XML without loading any DTD or external entity."""
    if not isinstance(data, bytes):
        _fail("config input must be bytes")
    if len(data) > MAX_BYTES:
        _fail("config exceeds 1 MiB")
    try:
        data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        _fail("config must be UTF-8 XML")
    parser = expat.ParserCreate(encoding="UTF-8")
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    stack = []
    roots = []
    count = 0

    def node():
        nonlocal count
        count += 1
        if count > MAX_NODES:
            _fail("config exceeds 4096 XML nodes")

    def start(name, attrs):
        node()
        if len(stack) + 1 > MAX_DEPTH:
            _fail("config exceeds XML nesting depth 16")
        if name not in {"plist", "dict", "array", "key", "string", "integer", "true", "false"}:
            _fail(f"unsupported plist element: {name}")
        if name == "plist":
            if stack or roots or attrs != {"version": "1.0"}:
                _fail("one root plist version=1.0 is required")
        elif attrs:
            _fail(f"attributes are not allowed on {name}")
        if not stack and name != "plist":
            _fail("root element must be plist")
        if stack and stack[-1][0] not in {"plist", "dict", "array"}:
            _fail("scalar plist elements cannot have child elements")
        stack.append([name, [], []])

    def chars(text):
        if stack:
            stack[-1][2].append(text)
        elif text.strip():
            _fail("text outside plist")

    def end(name):
        tag, children, parts = stack.pop()
        text = "".join(parts)
        if tag in {"dict", "array", "plist"} and text.strip():
            _fail("mixed text in plist container")
        if tag == "dict":
            if len(children) % 2:
                _fail("dictionary keys require values")
            value = {}
            for index in range(0, len(children), 2):
                key_tag, key = children[index]
                value_tag, item = children[index + 1]
                if key_tag != "key" or value_tag == "key":
                    _fail("dictionary requires alternating key/value elements")
                if key in value:
                    _fail(f"duplicate plist key: {key}")
                value[key] = item
        elif tag == "array":
            if any(kind == "key" for kind, _ in children):
                _fail("key element outside a dictionary")
            value = [item for _, item in children]
        elif tag == "plist":
            if len(children) != 1 or children[0][0] != "dict":
                _fail("plist must contain exactly one dictionary")
            value = children[0][1]
        elif tag in {"true", "false"}:
            if text:
                _fail("boolean plist elements must be empty")
            value = tag == "true"
        elif tag == "integer":
            literal = text.strip()
            if not re.fullmatch(r"0|[1-9][0-9]{0,19}", literal):
                _fail("integer must be canonical unsigned decimal")
            value = int(literal)
            if value > (1 << 64) - 1:
                _fail("integer exceeds uint64")
        else:
            value = text
        if stack:
            stack[-1][1].append((tag, value))
        else:
            roots.append(value)

    def declaration(version, encoding, standalone):
        if version != "1.0" or (encoding is not None and encoding.lower() != "utf-8"):
            _fail("only XML 1.0 UTF-8 is supported")

    def doctype(name, system, public, internal):
        if name != "plist" or system != PLIST_SYSTEM_ID or public != PLIST_PUBLIC_ID or internal:
            _fail("only the standard plist DOCTYPE without internal subset is allowed")

    def forbidden(*_):
        _fail("XML entities and processing instructions are forbidden")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = chars
    parser.XmlDeclHandler = declaration
    parser.StartDoctypeDeclHandler = doctype
    parser.EntityDeclHandler = forbidden
    parser.ExternalEntityRefHandler = forbidden
    parser.ProcessingInstructionHandler = forbidden
    parser.CommentHandler = lambda _: node()
    try:
        parser.Parse(data, True)
    except expat.ExpatError as exc:
        _fail(f"invalid XML at line {exc.lineno}, column {exc.offset}")
    if len(roots) != 1 or stack:
        _fail("one complete plist is required")
    return roots[0]


def _dict(value, keys, path):
    if type(value) is not dict:
        _fail(f"{path} must be a dictionary")
    expected = set(keys)
    if set(value) != expected:
        extra, missing = set(value) - expected, expected - set(value)
        _fail(f"{path} unknown keys={sorted(map(str, extra))}; missing keys={sorted(missing)}")
    return value


def _int(value, low, high, path):
    if type(value) is not int or not low <= value <= high:
        _fail(f"{path} must be an integer in [{low}, {high}]")
    return value


def _bool(value, path):
    if type(value) is not bool:
        _fail(f"{path} must be a boolean")
    return value


def _one(value, allowed, path):
    if type(value) is not str or value not in allowed:
        _fail(f"{path} must be one of {sorted(allowed)}")
    return value


def _text(value, path, limit=128):
    if type(value) is not str or not value or value != value.strip():
        _fail(f"{path} must be a nonempty bounded string without surrounding whitespace")
    try:
        if len(value.encode("utf-8")) > limit:
            _fail(f"{path} exceeds its UTF-8 byte limit")
    except UnicodeEncodeError:
        _fail(f"{path} is not valid Unicode")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        _fail(f"{path} contains a control character")
    return value


def _id(value, path):
    _text(value, path)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
        _fail(f"{path} is not a profile/object identifier")
    return value


def _guid(value, path):
    _text(value, path, 36)
    if not re.fullmatch(r"[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", value):
        _fail(f"{path} must be a canonical GUID")
    guid = uuid.UUID(value)
    if not guid.int:
        _fail(f"{path} must not be the zero GUID")
    return str(guid)


def _hash(value, path):
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        _fail(f"{path} requires an exact lowercase SHA-256")
    return value


def _resolve_profile(profile_id, require_metal, profiles):
    if profiles is not None and not isinstance(profiles, Mapping):
        _fail("guest profile registry must be a mapping supplied outside config")
    if profile_id == CONFORMANCE_PROFILE:
        if require_metal:
            _fail("conformance-only profile has no verified Metal adapter")
        return {"id": profile_id, "kind": "conformance", "execution_contract_verified": False}
    if profiles is None or profile_id not in profiles:
        _fail("Guest.ProfileID is not registered; a product name is not an exact guest profile")
    entry = _dict(profiles[profile_id], {"Kind", "BuildID", "ImageSHA256", "ABIVersion", "MMUGranule",
        "TimerFrequencyHz", "BootABI", "InterruptController", "SoCContract", "CPUFeatures", "GraphicsAdapter"}, "GuestProfile")
    _one(entry["Kind"], {"macos"}, "GuestProfile.Kind")
    build = _text(entry["BuildID"], "GuestProfile.BuildID")
    if not re.fullmatch(r"(?:25|26)[A-Z][0-9]+[a-z]?", build):
        _fail("GuestProfile.BuildID must identify an exact macOS 26/27 build")
    _hash(entry["ImageSHA256"], "GuestProfile.ImageSHA256")
    _int(entry["ABIVersion"], 1, 1, "GuestProfile.ABIVersion")
    if type(entry["MMUGranule"]) is not int or entry["MMUGranule"] not in (4096, 16384):
        _fail("GuestProfile.MMUGranule must be 4096 or 16384")
    _int(entry["TimerFrequencyHz"], 1, (1 << 32) - 1, "GuestProfile.TimerFrequencyHz")
    _one(entry["BootABI"], {"iBoot"}, "GuestProfile.BootABI")
    _one(entry["InterruptController"], {"AIC"}, "GuestProfile.InterruptController")
    _id(entry["SoCContract"], "GuestProfile.SoCContract")
    features = entry["CPUFeatures"]
    if type(features) is not list or not 1 <= len(features) <= 128:
        _fail("GuestProfile.CPUFeatures must be a bounded nonempty list")
    for feature in features:
        _id(feature, "GuestProfile.CPUFeatures")
    if len(set(features)) != len(features):
        _fail("duplicate GuestProfile CPU feature")
    adapter = entry["GraphicsAdapter"]
    metal = False
    if adapter is not None:
        _dict(adapter, {"ID", "SHA256", "SGPUABI", "MetalValidated"}, "GuestProfile.GraphicsAdapter")
        _id(adapter["ID"], "GuestProfile.GraphicsAdapter.ID")
        _hash(adapter["SHA256"], "GuestProfile.GraphicsAdapter.SHA256")
        _int(adapter["SGPUABI"], 1, 1, "GuestProfile.GraphicsAdapter.SGPUABI")
        metal = _bool(adapter["MetalValidated"], "GuestProfile.GraphicsAdapter.MetalValidated")
    if require_metal and not metal:
        _fail("Guest.RequireMetal requires a registered Metal-validated adapter declaration")
    return {"id": profile_id, "kind": "macos", "build_id": build,
            "execution_contract_verified": False, "registry_sha256": hashlib.sha256(
                json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def normalize_config(config: dict[str, Any], *, profiles: Mapping | None = None) -> dict[str, Any]:
    """Validate exact schema and return a detached normalized configuration."""
    _dict(config, {"SchemaVersion", "PlatformPolicy", "CPU", "Security", "Memory", "Storage", "Graphics", "Guest"}, "config")
    _int(config["SchemaVersion"], 1, 1, "SchemaVersion")
    _one(config["PlatformPolicy"], {"AppleIntelOnly"}, "PlatformPolicy")
    cpu = _dict(config["CPU"], {"MinimumISA", "Codegen", "HybridScheduling", "VCPUs", "ServiceLogicalCPUs", "SMTPolicy"}, "CPU")
    _one(cpu["MinimumISA"], {"sse4.2"}, "CPU.MinimumISA")
    _one(cpu["Codegen"], {"auto"}, "CPU.Codegen")
    _one(cpu["HybridScheduling"], {"capacity-aware"}, "CPU.HybridScheduling")
    _one(cpu["SMTPolicy"], {"isolate-cells"}, "CPU.SMTPolicy")
    if cpu["VCPUs"] != "auto":
        _int(cpu["VCPUs"], 1, MAX_CPUS, "CPU.VCPUs")
    _int(cpu["ServiceLogicalCPUs"], 1, MAX_CPUS, "CPU.ServiceLogicalCPUs")
    security = _dict(config["Security"], {"VMXRequired", "EPTRequired", "IOMMURequired", "InterruptRemappingRequired", "DMABypass"}, "Security")
    for key, value in security.items():
        expected = key != "DMABypass"
        if _bool(value, f"Security.{key}") is not expected:
            _fail(f"Security.{key} is immutable and must be {expected}")
    memory = _dict(config["Memory"], {"GuestMiB", "HostReserveMiB", "JITCacheMiB"}, "Memory")
    for key, value in memory.items():
        _int(value, 1, MAX_MIB, f"Memory.{key}")
    if memory["JITCacheMiB"] > memory["HostReserveMiB"]:
        _fail("Memory.JITCacheMiB is included in and cannot exceed HostReserveMiB")
    if memory["GuestMiB"] > MAX_MIB - memory["HostReserveMiB"]:
        _fail("combined memory reservation overflows uint64 bytes")
    storage = config["Storage"]
    if type(storage) is not list or not 1 <= len(storage) <= 32:
        _fail("Storage must have 1..32 explicit raw GPT partition bindings")
    disks, seen_ids, seen_partitions, normalized_storage = {}, set(), set(), []
    for index, item in enumerate(storage):
        path = f"Storage[{index}]"
        _dict(item, {"ID", "Backend", "DeviceSerial", "DiskGUID", "PartitionGUID", "SectorBytes", "ReadOnly"}, path)
        identifier = _id(item["ID"], path + ".ID")
        if identifier in seen_ids:
            _fail("duplicate Storage ID")
        seen_ids.add(identifier)
        _one(item["Backend"], {"raw-gpt-partition"}, path + ".Backend")
        serial = _text(item["DeviceSerial"], path + ".DeviceSerial", 255)
        disk = _guid(item["DiskGUID"], path + ".DiskGUID")
        partition = _guid(item["PartitionGUID"], path + ".PartitionGUID")
        if disk in disks and disks[disk] != serial:
            _fail("DiskGUID is bound to conflicting device serials")
        disks[disk] = serial
        if partition in seen_partitions:
            _fail("duplicate Storage PartitionGUID")
        seen_partitions.add(partition)
        if type(item["SectorBytes"]) is not int or item["SectorBytes"] not in (512, 4096):
            _fail(path + ".SectorBytes must be 512 or 4096")
        _bool(item["ReadOnly"], path + ".ReadOnly")
        normalized_storage.append({**item, "DiskGUID": disk, "PartitionGUID": partition})
    graphics = _dict(config["Graphics"], {"Device", "DriverPolicy", "MinimumProfile", "OnUnsupported"}, "Graphics")
    _one(graphics["DriverPolicy"], {"allowlist"}, "Graphics.DriverPolicy")
    _one(graphics["MinimumProfile"], {"display-only", "vfgp-base1"}, "Graphics.MinimumProfile")
    _one(graphics["OnUnsupported"], {"display-only", "halt"}, "Graphics.OnUnsupported")
    device = graphics["Device"]
    if device != "auto":
        limits = {"Segment":65535, "Bus":255, "Device":31, "Function":7, "VendorID":65535,
                  "DeviceID":65535, "SubsystemVendorID":65535, "SubsystemDeviceID":65535, "RevisionID":255}
        _dict(device, limits, "Graphics.Device")
        for key, high in limits.items():
            _int(device[key], 0, high, "Graphics.Device." + key)
        if device["VendorID"] in (0, 65535):
            _fail("Graphics.Device requires a real PCI vendor selector")
    guest = _dict(config["Guest"], {"ProfileID", "RequireMetal"}, "Guest")
    _id(guest["ProfileID"], "Guest.ProfileID")
    require_metal = _bool(guest["RequireMetal"], "Guest.RequireMetal")
    if require_metal and (graphics["MinimumProfile"] != "vfgp-base1" or graphics["OnUnsupported"] != "halt"):
        _fail("Metal-required guest needs vfgp-base1 and halt on unsupported graphics")
    _resolve_profile(guest["ProfileID"], require_metal, profiles)
    normalized = json.loads(json.dumps(config, ensure_ascii=False))
    normalized["Storage"] = normalized_storage
    return normalized


def load_config(path: str | Path, *, profiles: Mapping | None = None) -> dict[str, Any]:
    """Read at most 1 MiB+1; return hashes and M0-only normalized evidence."""
    source = Path(path)
    if not source.is_file():
        _fail("config path must be a regular file")
    with source.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    config = normalize_config(parse_xml(raw), profiles=profiles)
    encoded = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"config": config, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "normalized_sha256": hashlib.sha256(encoded).hexdigest(),
            "guest_profile": _resolve_profile(config["Guest"]["ProfileID"], config["Guest"]["RequireMetal"], profiles),
            "boot_authorized": False, "validation_level": "UNIT", "signature_verified": False,
            "hardware_measured": False}
