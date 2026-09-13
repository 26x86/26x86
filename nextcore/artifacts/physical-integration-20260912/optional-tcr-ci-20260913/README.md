# Optional TCR and hierarchy: fresh CI receipts

These six JSON files were copied byte-for-byte from freshly downloaded authored CI evidence and its independent immutable-source verification. No binaries, private original kernel inputs, or downloaded manuals are included.

The tested parent is `b18e6d648874a8f4179498c4f3639e75f1bdc593`, with ISE `3a0ed3dd39f78fc3c55415f898d7faa8f34699c2` and EFI `1dc49ce712b35cf37cd58571130972dfae7b28e5`. Workspace [34715223879](https://github.com/26x86/26x86/actions/runs/34715223879) passed all six jobs; Sandbox [34715223874](https://github.com/26x86/26x86/actions/runs/34715223874) passed both jobs; documentation [34715223896](https://github.com/26x86/26x86/actions/runs/34715223896) passed. The execution receipts come from the workspace run's `nextcore-x86-efi-stage1` artifact. This receipt-only publication does not change the runtime package source pin.

## Scope of verification

- Optional TCR: 160 C assertions, 102 Rust bank tests and 102 direct MMU tests passed. The Rust suites overlap; they are not 204 unique new cases. The receipt retains the service-profile rejection checks and source preservation.
- Hierarchy native: 34 provider tests in each of cached, uncached and small-slot modes; 104 reference tests passed with source preservation.
- Actual Arm hierarchy: 306 authored cases. The native direct comparison joins 258 AP/XN/ancestor rows and checks outcomes and fault syndromes. The other 48 Arm rows are not included in this direct join.
- EFI hierarchy: 961 authored cases passed, assembly matched, before/after input hashes matched, and the process and process group were reaped.

`verification.json` independently compares exactly the hashes declared by these receipts with immutable module Git archives: 82 optional-TCR source/test paths, 132 native-hierarchy source paths, five Arm-oracle source paths, and three EFI probe/verifier/fixture paths. These sets overlap and do not cover every repository file. It also verifies that the native comparison's Arm-receipt SHA256 matches the downloaded Arm receipt. EFI binary preservation within the run is checked; the binary is not a Git blob and no repository-byte comparison is claimed for it.

The copied verification file retains relative scratch artifact paths and hashes for other downloaded receipts. Those entries are provenance, not a claim that every referenced receipt is included in this deliberately minimal package. The six included JSON files retain their original content and recorded absolute CI acquisition paths.

`manifest.json` lists every included payload file's byte length and SHA256, including this README. `manifest.sha256` binds that manifest. Copies were compared to their downloaded source bytes and all payload hashes were rechecked. Physical installed-macOS startup and physical display remain unverified.
