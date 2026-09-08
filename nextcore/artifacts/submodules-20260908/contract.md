# Actual Git submodule integration

Current state: seven independently versioned repositories exist, but the parent
contains 134 copied crate files. Desired state: exactly seven gitlinks own the
crates and a fresh recursive clone builds the same reviewed source.

DECIDED: retain each existing module history and working source, replace parent
source index entries with gitlinks, record public HTTPS URLs in .gitmodules,
and patch remote Cargo dependencies to the local workspace modules. Standalone
dependencies pin immutable module commits. Copy existing module license,
workflow and provenance files into their own checkouts. Update provenance for
new source commits rather than claiming old hash inventories cover new edits.

All checkout workflows initialize recursively. A verifier requires exactly the
expected gitlinks, exact checkout SHAs, expected origins, no private tracked
paths, and (when requested) exactly seven local Cargo packages and clean module
worktrees. Parent publication requires reachable module commits. Preserve old
remote histories and tags. No original IPSW or derived binary enters any module.

Validation: workspace and independent module builds, both EFI targets, real
authored firmware tests where supported, and a fresh recursive clone resolving
the published module branches. Original-kernel and Metal acceptance remain
separate runtime requirements.


Runtime ownership: the existing C x86 JIT and no_std ARM architectural reference
move into the ISE module under runtime/. The parent retains integration scripts;
it does not keep a second source copy. EFI consumes the module as a host build
dependency and locates shipped C files through EFI_RUNTIME_DIR, without requiring
an adjacent sibling checkout in an independent EFI clone. Root owns relocation
once CPU/GPU/EFI authors freeze their source. Host compiler/protection/GOP adapters
are freestanding PE/COFF inputs, not a Linux process inside the product.
