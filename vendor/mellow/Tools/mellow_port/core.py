"""Deterministic source manifests, lexical dependency inventories and review output."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat


class PortError(ValueError):
    pass


RECIPES_PATH = Path(__file__).resolve().parents[2] / "porting/backend-recipes.json"
SUPPORTED = {".c", ".h", ".cc", ".cpp", ".hpp", ".inc"}
SKIP_CALLS = {"if", "for", "while", "switch", "return", "sizeof", "typeof", "__typeof__", "alignof", "_Static_assert"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def no_links(path):
    """Reject symlinks and Windows reparse points in every existing component."""
    path = Path(os.path.abspath(path))
    for component in [*reversed(path.parents), path]:
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise PortError("Symlink/reparse point is not admitted: " + str(component))
    return path


def source_file(root, relative):
    if "\\" in relative or PureWindowsPath(relative).drive or not re.fullmatch(r"[A-Za-z0-9_./+-]+", relative):
        raise PortError("Use a relative POSIX source path")
    item = PurePosixPath(relative)
    if item.is_absolute() or not item.parts or any(part in ("..", ".") for part in relative.split("/")):
        raise PortError("Source path must stay within its root")
    if item.suffix.lower() not in SUPPORTED:
        raise PortError("Only source text is admitted; .ko/.run/binaries are unsupported")
    path = no_links(root.joinpath(*item.parts))
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise PortError("Source is missing or outside the admitted root")
    if path.stat().st_size > 16 * 1024 * 1024:
        raise PortError("Source file exceeds the 16 MiB intake bound")
    data = path.read_bytes()
    if b"\0" in data:
        raise PortError("Binary source input is unsupported")
    try:
        return item.as_posix(), data, data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PortError("Source must be UTF-8 text") from error


def strip_comments(text):
    # C comments separate tokens. Retain whitespace and source line positions;
    # removing a comment entirely would turn e.g. 1/**/2 into literal 12.
    return re.sub(r"/\*.*?\*/|//[^\n]*", lambda m: " " + "\n" * m[0].count("\n"), text, flags=re.S)


def lexical(text):
    text = strip_comments(text)
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)


def license_facts(text):
    found = []
    for line in text.splitlines():
        if "SPDX-License-Identifier:" in line:
            expression = line.split("SPDX-License-Identifier:", 1)[1].strip().removesuffix("*/").strip()
            if expression and re.fullmatch(r"[A-Za-z0-9.+() :_-]+", expression):
                found.append(expression)
    found = sorted(set(found))
    expression = found[0] if len(found) == 1 else None
    notices = sorted(set(line.strip().strip("/* ").replace("*/", "* /") for line in text.splitlines() if re.search(r"\bcopyright\b", line, re.I)))
    return {"spdx_expressions_observed": found, "single_expression": expression, "copyright_notices_observed": notices,
            "missing_or_conflicting": expression is None,
            "gpl_component_review_required": any("GPL" in item for item in found),
            "license_compatibility_determined": False,
            "note": "SPDX text is recorded, not legal clearance; preserve upstream notices and review distribution obligations."}


def inventory(relative, text):
    code = lexical(text)
    includes = sorted(set(re.findall(r'^\s*#\s*include\s*[<"]([^>"\n]+)[>"]', text, re.M)))
    definitions = sorted(set(re.findall(r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", code)) - SKIP_CALLS)
    calls = sorted(set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", code)) - SKIP_CALLS)
    constants, rejected = [], []
    uncommented = strip_comments(text)
    for number, line in enumerate(uncommented.splitlines(), 1):
        macro = re.match(r"^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$", line)
        if not macro:
            continue
        name, tail = macro.groups()
        value = tail.strip()
        match = re.fullmatch(r"(0[xX][0-9a-fA-F]+|0|[1-9][0-9]*)([uUlL]*)", value) if tail[:1].isspace() else None
        suffix_ok = match and re.fullmatch(r"(?:[uU](?:[lL]|ll|LL)?|(?:[lL]|ll|LL)[uU]?)?", match[2])
        if suffix_ok:
            number_value = int(match[1], 16 if match[1].lower().startswith("0x") else 10)
            if number_value <= 0xFFFFFFFFFFFFFFFF:
                constants.append({"name": name, "literal": value, "unsigned_value": number_value, "line": number})
                continue
        if value:  # include guards are not missing register implementations
            rejected.append({"name": name, "line": number, "reason": "Not an unambiguous standalone integer literal; no expression evaluation or macro expansion performed."})
    return {"path": relative, "includes_lexical": includes, "function_definitions_approximate": definitions,
            "call_tokens_approximate": calls, "simple_integer_defines": constants, "unconverted_macros": rejected,
            "limitations": "Lexical inventory only; includes in comments/disabled blocks and macro calls may appear. No preprocessing, type analysis, dependency resolution or function porting."}


def prepare(command, source_root, target, revision, files, output, source_url=None, require_ready=False):
    if command not in ("inspect", "plan", "generate"):
        raise PortError("Unknown operation")
    recipe_bytes = RECIPES_PATH.read_bytes()
    recipes = json.loads(recipe_bytes)["recipes"]
    if target not in recipes:
        raise PortError("An explicit supported target recipe is required")
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", revision):
        raise PortError("Revision must be a full 40/64 hexadecimal immutable source identifier")
    if not files:
        raise PortError("At least one explicitly selected --file is required")
    root = no_links(Path(source_root))
    if not root.is_dir():
        raise PortError("Source root is not a directory")
    out = no_links(Path(output))
    if out.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(out.resolve()):
        raise PortError("Output and source trees must not overlap")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise PortError("Output must be a new or empty directory; existing files are never overwritten")
    recipe = recipes[target]
    manifest_files, inventories = [], []
    for relative in sorted(set(files)):
        name, data, text = source_file(root, relative)
        if not any(name.startswith(prefix) for prefix in recipe["source_prefixes"]):
            raise PortError("Source path is outside the selected recipe: " + name)
        facts = license_facts(text)
        manifest_files.append({"path": name, "sha256": digest(data), "size_bytes": len(data), "license": facts})
        inventories.append(inventory(name, text))
    if not any(item["path"].startswith(prefix) for item in manifest_files for prefix in recipe["admission_prefixes"]):
        raise PortError("Selection does not contain a source from the selected backend")
    source_pin = digest(canonical(manifest_files).encode())
    manifest = {"schema_version": 1, "target": target, "source_revision_claim": revision.lower(),
                "revision_membership_verified": False, "revision_note": "The revision is a caller-supplied provenance label; per-file SHA256 pins are measured. A Git/archival attestation is still required.",
                "source_url_claim": source_url, "content_pin_sha256": source_pin,
                "recipe_sha256": digest(recipe_bytes), "files": manifest_files}
    gaps = [{"id": "source-attestation", "layer": "source provenance", "status": "unresolved", "detail": "Verify selected content against the claimed immutable upstream revision."},
            {"id": "xnu-services", "layer": "kernel/IOKit", "status": "unimplemented", "detail": "Implement DMA/IOMMU ownership, mapping, synchronization, workqueues, allocator and Linux/DRM contract replacements."},
            {"id": "hardware-backend", "layer": "GPU kernel backend", "status": "unimplemented", "detail": recipe["focus"]},
            {"id": "userspace-abi", "layer": "IOAccelerator and userspace", "status": "unimplemented", "detail": "Establish a measured Tahoe kernel/user ABI, resource lifetime and command validation contract."},
            {"id": "workload-translation", "layer": "Metal/OpenGL/OpenCL userspace", "status": "unimplemented", "detail": "Implement API semantics, shader compilation and backend execution; source intake emits none of these."},
            {"id": "runtime-acceptance", "layer": "physical hardware", "status": "not_run", "detail": "Require measured PCI identity, real submission/fence, compute/readback and reset-free stress evidence."}]
    for item, inv in zip(manifest_files, inventories):
        if item["license"]["missing_or_conflicting"] or item["license"]["gpl_component_review_required"]:
            gaps.append({"id": "license:" + item["path"], "layer": "source licensing", "status": "review_required", "detail": item["license"]})
        if inv["function_definitions_approximate"] or inv["call_tokens_approximate"]:
            gaps.append({"id": "functions:" + item["path"], "layer": "kernel port", "status": "unimplemented", "detail": "No function body is translated or replaced by a success stub.", "definitions_approximate": inv["function_definitions_approximate"], "call_tokens_approximate": inv["call_tokens_approximate"]})
    capabilities = {"source_inspection": "implemented", "dependency_inventory": "lexical_only", "port_plan": "implemented",
                    "simple_integer_extraction": "implemented", "driver_compilation": "unavailable", "xnu_gpu_backend": "unimplemented",
                    "workload_translation": "unimplemented", "hardware_execution": "not_run", "driver_ready": False}
    plan = {"schema_version": 1, "concept": "Metal Emulation Layer Logic for OpenGL/OpenCL Workloads", "target_recipe": target,
            "recipe": recipe, "content_pin_sha256": source_pin, "capabilities": capabilities,
            "required_work": gaps, "generation_scope": "Review-only integer macro extraction and build metadata; no working driver or API compatibility implied."}
    artifacts = {"source-manifest.json": canonical(manifest), "inventory.json": canonical({"schema_version": 1, "files": inventories}),
                 "plan.json": canonical(plan), "gap-report.json": canonical({"driver_ready": False, "ready_gate": "fail", "gaps": gaps})}
    if command == "generate":
        exports = []
        for item, inv in zip(manifest_files, inventories):
            expression = item["license"]["single_expression"]
            if expression is None:
                continue  # no source-derived output with missing/conflicting license facts
            extracted = inv["simple_integer_defines"]
            if not extracted:
                continue
            path_pin = digest(item["path"].encode("utf-8"))
            slug = re.sub(r"[^A-Za-z0-9_]", "_", Path(item["path"]).stem) + "_" + path_pin[:12] + "_" + item["sha256"][:12]
            lines = ["/* SPDX-License-Identifier: " + expression + " */", "/* Review-only extraction. Preserve and review upstream notices before redistribution.",
                     " * Source: " + item["path"], " * SHA256: " + item["sha256"], " * Constants may come from inactive preprocessor branches. No register suitability asserted.", " */"]
            lines.extend("/* " + notice + " */" for notice in item["license"]["copyright_notices_observed"])
            lines.append("#pragma once")
            for constant in extracted:
                # Namespaced per file and line: repeated conditional macro names cannot silently collide.
                name = "MELLOW_SOURCE_" + slug.upper() + "_L" + str(constant["line"]) + "_" + constant["name"]
                lines.append("#define " + name + " " + constant["literal"] + " /* source line " + str(constant["line"]) + " */")
            dest = "generated/" + slug + ".h"
            artifacts[dest] = "\n".join(lines) + "\n"
            exports.append({"path": dest, "source": item["path"], "constant_count": len(extracted)})
        artifacts["backend.json"] = canonical({"target": target, "content_pin_sha256": source_pin, "capabilities": capabilities, "review_headers": exports, "implemented_entry_points": [], "pci_device_ids": []})
        artifacts["CMakeLists.txt"] = 'cmake_minimum_required(VERSION 3.20)\nproject(MellowSourceReview LANGUAGES NONE)\n# Integrate reviewed constants only after the kernel and userspace gaps are implemented.\nmessage(FATAL_ERROR "This is source review output, not a compilable XNU GPU driver. See gap-report.json.")\n'
    artifacts["artifact-manifest.json"] = canonical({"schema_version": 1, "operation": command, "files": [{"path": name, "sha256": digest(content.encode())} for name, content in sorted(artifacts.items())], "success_meaning": "Requested review artifacts generated; driver readiness remains false."})
    out.mkdir(parents=True, exist_ok=True)
    for name, content in sorted(artifacts.items()):
        destination = out / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    return {"operation": command, "artifacts_generated": True, "target": target, "content_pin_sha256": source_pin, "driver_ready": False, "compile_performed": False, "hardware_test_performed": False, "exit_code": 2 if require_ready else 0}
