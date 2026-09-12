# Mac hardware catalog method

Current Status: The September 12, 2026 snapshot contains 396 catalog records across 20 families: 175 unique model identifiers and 221 name-based records. Seven Apple identification pages are reconciled with the repository's historical SMBIOS data; historical Apple technical specifications supply 220 named records. No catalog entry has physical Nextcore macOS boot evidence.

Target State: A searchable catalog spanning real Mac families, with explicit architecture, source-backed hardware details, Apple operating-system eligibility, and independently recorded Nextcore execution evidence.

## Contract

`data/mac-models.json` uses schema `nextcore.mac-model-catalog.v1`. Each `models` entry has a stable `id`, display `name`, `family`, nullable `year`, `identifiers`, `architecture`, `apple_support`, `nextcore`, `sources`, and `notes`. `catalog_level` distinguishes `model-identifier` from `named-model`. Modern identifier entries use a lowercased identifier with a hyphen replacing its comma. Historical named entries use `legacy-` followed by the Apple specification page number. MacBook Neo uses `macbook-neo-2026` until an exact official identifier is verified; its identifier array is empty.

Entries are grouped by model identifier or named historical specification, not sales SKU. A model identifier can represent multiple release dates, enclosures, or configurable hardware: `variants` preserves those source records. Unknown values are JSON `null`, never invented defaults. A year extracted from a source title or introduction field is not an inferred support cutoff.

Apple's identification pages govern reconciled names, years, identifiers and linked technical specifications. Historical repository data supplements identifiers omitted from those pages; its provenance is explicitly marked as repository data rather than Apple verification. Internal/development/virtual model entries are excluded. Hardware configuration lists represent known options, not a guarantee about an individual machine. Serial numbers and device-specific identifiers are neither required nor collected.

Apple's macOS 27 eligibility is recorded separately from the newest released system named on an identification page. The official macOS page is the eligibility source; a model listing Tahoe does not contradict a preview eligibility announcement. `nextcore.status` remains `unverified` until a model-specific physical installed-system reboot and desktop receipt exists. CI, unit tests, OVMF, EFI menus and an Apple support listing cannot set that status to supported.

## Coverage boundary

| Architecture | Records | Scope |
| --- | ---: | --- |
| Intel | 121 | Model identifiers, including Xserve |
| Apple silicon | 55 | 54 model identifiers and MacBook Neo by name |
| PowerPC | 154 | Named historical models/configurations |
| Motorola 68k | 66 | Named historical models/configurations |

The catalog covers MacBook, MacBook Air, MacBook Pro, MacBook Neo, Mac mini, Mac Studio, Mac Pro, iMac, iMac Pro, Xserve, Power Mac, PowerBook, iBook, eMac, Macintosh, LC, Centris, Quadra, Performa, and Twentieth Anniversary Macintosh. Apple pages verify 144 of the 175 modern identifiers; 31 are preserved only from the explicitly attributed repository dataset. Duplicate source dictionary keys and `_v2`/`_v3` board variants are preserved within their owning model, not counted as additional identifiers. Internal, developer, virtual-machine and bridge-only entries are excluded.

The generator follows 86 historical documentation directories, including [Earlier Desktops](https://support.apple.com/en-us/docs/mac/pp210), [Earlier Power Mac](https://support.apple.com/en-us/docs/mac/pp201), and [Earlier PowerBooks](https://support.apple.com/en-us/docs/mac/pp212). It opens the linked specification pages and classifies the primary architecture from documented processor fields or explicit processor-family names. Four docking accessories are excluded. Historical DOS-compatible coprocessors do not turn the primary Mac into an Intel Mac. Legacy records have `nextcore.architecture_support: not-implemented`; inclusion is an inventory entry, never an assertion that Nextcore runs on those architectures.

A bounded follow-up checked the public directory HTML for next-page and load-more links/buttons; none were present. The inspected lists contain 50 specification links each, so that observation does not establish completeness. Public Apple search results separately supplied Macintosh II, IIx, IIcx, IIsi, IIfx, SE/30, Classic II, Color Classic and Color Classic II. These nine additions use actual opened Apple specification URLs. No pagination endpoint or numeric article ID was guessed. Validation now guards 128K, 512K, Plus, SE, SE/30, II, IIci, Portable, IIfx and Color Classic II as historical sentinels. Further missing variants remain an open inventory task.

This is not a claim to enumerate every regional order number, build-to-order configuration or all Macintosh models since 1984. Some Apple historical directories expose a limited initial list. Missing historical revisions, educational/server variants, regional names and unlisted specification pages remain coverage gaps. The generated `coverage` object records source hashes, discovered counts, exclusions, fetch failures and repository-only identifiers. These gaps must remain visible in a checker and must not be displayed as a complete all-Mac certification.

## Hardware detail interpretation

`variants[].facts` contains fields explicitly printed on the identification page. `technical_specifications` records numeric memory/storage capacity mentions and processor names from 129 linked specification pages. Those pages can cover several identifiers, such as both Max and Ultra configurations of a Mac Studio. Capacity mentions are **not** a Cartesian product of valid configurations or the installed hardware in the selected machine. Blank extraction is unknown, not zero. Full CPU/GPU variants, per-port capabilities, upgrade limits and regional SKU mapping are not exhaustively normalized.

`repository_hardware` retains public historical CPU-generation enum spellings, stock GPU/storage options, networking and display-size metadata with repository provenance. It is not newly verified Apple technical data. The repository's old `Max OS Supported` field is intentionally not used as the official OS-support authority.

The [official macOS 27 page](https://www.apple.com/os/macos/) lists the eligible Apple-silicon families, including the 2023 Mac Pro. `apple_support.macos_27` records that eligibility. `apple_support.latest_macos` records only the released system stated on a checked identification page and can be null. These are different claims. Neither authorizes a Nextcore boot-success label. Apple's eligibility also does not guarantee every OS feature on every eligible configuration.

## Reproduction and verification

The generator uses Python, `requests` and `beautifulsoup4`. From the repository root:

```text
python Tools/build_mac_catalog.py --check
python Tools/build_mac_catalog.py --cache ../mac-catalog-cache --refresh
```

Keep the HTML cache outside the published tree. The generator parses the historical Python dataset as an AST without importing or executing its platform-dependent modules. A refresh fetches public HTML; it does not download product images. Reusing the cache reproduces source parsing; `--refresh` is required before treating a later run as newly checked Apple information. Source-content SHA-256 values are retained in the catalog; hashes prove input identity, not Apple authenticity or hardware execution.

Validation checks unique stable IDs and model identifiers, minimum coverage, architecture/status separation, essential old/new model sentinels, sources, and absence of fabricated Nextcore boot evidence. The identification parser rejects a page if any listed model identifier was lost. The September 12 follow-up fetched all 224 discovered legacy specification pages, excluded four accessories, and completed all 129 modern specification fetches. One initially unavailable page (`111932`) was recovered on a later public fetch. An unavailable source is recorded explicitly rather than erasing its model or inventing missing detail. This is a data-validation receipt only; physical boot, firmware, display, input, storage and installed-system reboot remain separate acceptance gates.

OPEN_QUESTION: Inventory: Expand beyond the discovered historical directory lists and reconcile missing Macintosh variants without inventing modern identifiers.
OPEN_QUESTION: Inventory: Verify MacBook Neo's exact public model identifier before filling its empty identifier array.
