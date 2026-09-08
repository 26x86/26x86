# x86 EFI ARM64e execution — QARMA5 integration

The user's final target is an x86 EFI compatibility/JIT layer. WSL and QEMU
are build and differential-test environments. The implementation replaces the
reference `arch.rs` PAC stub and connects the same allocation-free `pauth.rs`
provider to the actual C x86 JIT dispatcher. The ISE module owns these runtime
sources; the EFI module owns caller memory, image loading and lifecycle.

Implement QARMA5 as nibble-array permutations/substitution/matrix operations
from the public cipher specification, independently expressed in Rust.
Validate against QEMU architectural instruction execution. Add all five
architectural 128-bit PAC key banks and the EL1 QARMA5 address-authentication
subset: PAC/AUT instruction/data A/B, zero/SP hints, XPAC and authenticated
branch/call/return. The initial pointer policy requires EL1, 48-bit lower or
upper virtual ranges with TBI disabled. Other address sizes/tag modes or EL2/3
instruction contexts return an explicit unsupported/undefined fault. Failed
authentication produces architectural v8.3 poisoned pointers; it never strips
the signature and treats failure as success. Features beyond this subset
remain unadvertised. QARMA3, FPAC, PACGA and enhanced PAuth are separate work.

Expose a boot runner over caller-owned, nonzero-base guest RAM with explicit
entry, x0 boot arguments and stack; bounds are checked before changing CPU
state, images are not copied or rewritten by execution. Existing diagnostic
copy-and-run behavior remains available. Generated x86 blocks execute ordinary
instructions; unsupported PAC/key-register instructions invoke the software
provider, commit architecture state only on success, and resume native JIT
execution. QEMU serves only as a differential oracle.

The C path currently requires guest MMU disabled and rejects SCTLR.M=1 without
committing it. The Rust reference core has its separate existing MMU path.
PAC handling requires EL1 and 48-bit T0SZ/T1SZ for the selected address range,
with TBI0/TBI1 and DS disabled. Advertising baseline APA=1 does not claim
complete ARM64e ABI support, Apple CPU implementation features or macOS boot.

## Executed evidence, 2026-09-08

- `efi-native-pauth-proof-r2.json`: rebuilt relocated ISE sources and passed
  84 existing native assertions, 23 nonzero-address boot assertions and 17
  native JIT plus Rust PAC assertions, with Linux `mprotect` enforcing W^X.
- The PAC fixture retires 22 instructions at guest PA `0x800000000`, writes
  APIA key words, configures SCTLR/TCR, signs `0x130` with modifier `0x9876`,
  observes `0xbf36000000000130`, authenticates back to `0x130`, and stores both
  values in caller RAM. With the callback absent it traps at the key write
  after eight retired instructions.
- The relocated Rust reference suite passes 59 tests. Primitive tests include
  eight PACGA upper-32-bit QARMA5 observations from QEMU 8.2.2, recorded in
  `qarma5-qemu-oracle.json`; `qarma5-qemu-oracle.S` is authored assembly.
  The oracle CPU was `max,pauth=on,pauth-impdef=off,cntfrq=24000000` on
  `virt,secure=off,virtualization=off`, not the unavailable patched VMApple
  binary. QEMU image/code hashes are included in the vector receipt.
- The initial probe receipt without `-r2` records a harness source-inventory
  failure (a nonexistent `arch.h`), corrected before the successful run.

Reproduce the native tests from repository root on Linux x86_64 / WSL2:

```sh
RUSTUP_TOOLCHAIN=stable python3 nextcore/tools/probe_efi_native_pauth.py \
  --rustc "$HOME/.cargo/bin/rustc" --output /tmp/fresh-native-pauth-proof.json
```

These are authored CPU/JIT execution proofs; original macOS kernel execution,
boot completion and Metal acceleration require separate integration evidence.

Sources: [QARMA cipher paper](https://eprint.iacr.org/2016/444),
[Arm architectural reference](https://developer.arm.com/documentation/ddi0487/latest),
[QEMU PAuth reference](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/target/arm/tcg/pauth_helper.c).
No Apple implementation, media or firmware bytes are included.
