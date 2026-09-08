# BP30 recursive integration evidence

A fresh recursive checkout of ea0a62e8e75efd517702873535dc1dfb0ffc6b42
passes the complete integration driver. Four changed module PRs are merged on
their independent main branches; the parent retains their immutable tested heads.
Seven repositories and seven workspace members resolve eight owned Rust packages.
The auxiliary memory service exists only in the ISE module.

The run passes 476 workspace tests, 149 Python tests, 25 GUI tests, 91
architectural reference tests, 158 captured Arm fault comparisons plus the
prior 18 MMU oracle cases, native scalar/pair/PAC/provider/ABI checks, 119 Vulkan
tests, compiled firmware packaging and Clippy. All build commands and statuses
are preserved in report.json. Validation.json identifies each integrated EFI.

Actual x86 OVMF executes 65 authored firmware cases: the existing 39, 23 Rust
memory-provider cases, two bounded-tier firmware cases and one successful direct
execution rejected as a provider bypass. Six additional CLI rejections are not
counted as firmware execution. The combined tier requires exactly 256 fetches,
native entries and retired instructions. A separate historical and standalone
combined bundle records the mutated callback-failure firmware; this fresh runner
does not claim to execute that variant.

The package policy includes an actual temporary Git/Cargo duplicate-resolution
negative control. The bypass regression rejects missing, malformed or unrelated
failure receipts, rather than accepting arbitrary child exit status 1. The final
review identified a README reproduction-path typo; its correction changes only
that README and its index entry, preserving historical execution/source receipts.

Final evidence and documentation receive their own exact-head canonical GitHub
recursive clone and CI checks before merge. These local integration receipts do
not claim that separate network check occurred on the implementation commit.
Native M=1 execution, exact macOS 27 startup ABI and live-state providers, normal
macOS boot and guest Metal remain incomplete.
