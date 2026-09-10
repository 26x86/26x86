# Isolated Asset Inventory (Inventory Slot)

## Responsibility

Records *metadata only* for assets located in the root `_isolated/` directory. Proprietary file contents, decrypted binaries, keys, and internal structures must NEVER be recorded in this document.

## Operating Rules

- In accordance with AGENTS.md §0 and PUBLIC_VS_PRIVATE_BOUNDARY.md:
  - Public code must never import, link, or include files from `_isolated/`.
  - The `_isolated/` folder is excluded from Git via `.gitignore` and protected by pre-commit hooks.
  - Knowledge transfer is restricted to high-level functional requirements rephrased in natural language.

## Asset Registry

| Identifier | Source Category | Ingestion Date | Retention Rationale |
|------------|-----------------|----------------|---------------------|
| `REF-XNU-BOOT-01` | Public Technical Reference | 2026-09-07 | Public XNU bootloader header analysis (`pexpert/i386/boot.h`) |
| `REF-DT-SPEC-01` | Open Specification | 2026-09-07 | Open Firmware IEEE 1275 device tree binding conventions |
| `REF-ACPI-SPEC-01` | Industry Specification | 2026-09-07 | UEFI Forum ACPI 6.5 table structure definitions |
| `REF-SMBIOS-01` | Industry Specification | 2026-09-07 | DMTF SMBIOS 3.7.0 system information structures |
