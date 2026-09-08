# Native flags, conditional branches and explicit diagnostic registers

Build Plan BP25-B establishes the SPTM handoff investigation separately from
legacy boot-argument placement. This ISE change implements generic AArch64
instructions and an explicit caller register interface; it does not create
SPTM arguments, memory services or a monitor.

The x86 translator now executes 32/64-bit ADD/SUB immediate with optional
NZCV updates, including CMP/CMN aliases, and all 16 B.cond encodings. It stores
guest flags explicitly, preserves other PSTATE fields and handles subtraction
carry as no-borrow. Branches read guest NZCV across generated block boundaries.
The independently unsupported FEAT_HBC encoding remains an instruction fault.

`vf_boot_run_with_registers` accepts caller-supplied x0 through x3 while the
legacy bridge retains x0=boot_args behavior. It does not dereference those
registers during initialization or assert that their argument objects exist.

`efi-native-flags-proof.json` records rebuilding ISE-owned runtime sources:
827 new native assertions, 84 prior JIT assertions, 23 boot assertions and
17 JIT/PAC assertions passed. Cases cover every condition against all 16 NZCV
values, integer carry/overflow, 32-bit zero extension, SP versus ZR, negative
branch displacements, flag preservation, exact budget and trap boundaries.
All execute under Linux W^X memory protection. Updated JIT and bridge sources
also compile freestanding to Win64 COFF for the EFI frontend.

The original SPTM entry and its next unsupported system-register boundary are
checked by the separate EFI diagnostic. The native results above contain no
Apple instruction fixture and do not claim macOS boot completion.

The subsequent private original-input EFI diagnostic retired four instructions
in three generated x86 blocks and stopped at the TPIDR_EL0 write boundary.
Independent checking confirmed the fault corresponds to the unchanged source
at entry + 48 bytes. x0 through x3 were preserved, and no boot-argument object
was dereferenced by this prefix. SPTM arguments and services remain unprovided.

`efi-native-fault-result-proof.json` supersedes the earlier native receipt for
the result-field clarification: `fault_instruction` now carries zero on exits
without a decoded synchronous fault. All four suites pass (84, 34, 17 and 827
assertions). Added cases exercise stale instruction state before HALT, budget,
code-capacity and host-protection exits, while retaining genuine trap words.

Reproduce from the ISE repository directory:

```sh
RUSTUP_TOOLCHAIN=stable python3 tools/probe_efi_native_pauth.py \
  --rustc "$HOME/.cargo/bin/rustc" --output /tmp/fresh-native-flags-proof.json
```
