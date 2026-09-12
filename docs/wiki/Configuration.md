# Application and EFI configuration

**Current Status:** Application schema verified against x86/settings.py and x86/paths.py.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Application settings, OpenCore plist configuration and NextCore firmware runtime
selectors are different contracts. A setting in one does not provision another.
See [current progress](../progress.md) before enabling experimental execution.

## Application settings

The current `x86/settings.py` store uses JSON with flat field names. Its defaults
include the following; this is a settings example, not a hardware profile:

```json
{
  "version": 1,
  "execution_mode": "native",
  "auto_patch": false,
  "verbose_logging": false,
  "last_detect": null,
  "auto_pre_avx_patch": true,
  "safari26_preavx_fix": true
}
```

`auto_pre_avx_patch` is the current key; `safari26_preavx_fix` is a legacy alias.
An enabled setting does not prove a particular kext was loaded or a crash fixed.
Nested `General`/`Hardware` examples from earlier documentation are not this
store's schema. The settings store does not read/write OCLP legacy plists.

| Host | Default config |
| --- | --- |
| macOS | `~/Library/Application Support/26x86/config.json` |
| Windows | `%APPDATA%\26x86\config.json` |
| Linux | `$XDG_CONFIG_HOME/26x86/config.json`, defaulting to `~/.config/26x86/config.json` |

Paths come from `x86/paths.py`. The documented GUI backend selector is
`X86_GUI_BACKEND`; consult the selected backend's implementation and diagnostics
for available runtimes. This page does not advertise unimplemented generic
`X86_CONFIG_PATH` or `X86_LOG_LEVEL` overrides.

## Firmware configuration

Use the exact schema and complete referenced file bundle for the selected EFI
build. Review the actual target ESP before deployment; never copy a sample disk
identifier. Model spoofing does not change physical hardware, and feature flags
do not waive missing runtime providers. See [OpenCore integration](OpenCore.md),
[Module repositories](Nextcore-Modules.md) and [Migration](Migration.md).

## Current evidence and hardware coverage

Reviewed for documentation freshness on 2026-09-12. See the
[portal](../index.md), [progress](../progress.md),
[compatibility catalog](../compatibility.md) and
[library](../library.md) for the active evidence boundary. Historical
receipts in this guide retain their original scope and date.
