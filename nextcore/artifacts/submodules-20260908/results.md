# x86 EFI ARM64e integration — 2026-09-08

The physical computer is x86. The target is a macOS-focused ARM64e-to-x86_64
JIT and hardware compatibility layer running directly in EFI. M1 is the ARM
platform baseline. WSL2 provides development tools; QEMU/OVMF is a firmware
test fixture.

Seven real Git submodules now own the implementations and histories. The parent
owns integration, tools and public evidence. All 134 formerly tracked crate files
remain present in module checkouts; 24 previously tracked freestanding runtime
files moved into ISE. Independent module manifests pin remote Git commits, and
the parent workspace resolves exactly seven local modules without duplicate
Nextcore dependency copies.

| Module | Integrated commit |
| --- | --- |
| Core | `1c1630fa8dc4d38198c94ae407fe4d6f2fcefdd9` |
| EFI | `b66d05bdfa82f5e11993beef1c860ed4965b4287` |
| Tool | `b10e7b94d0271ed7d27ecb9c8e2ccde2ca98a8f5` |
| ISE | `37a94d8af2a1014b90385d8c9f3ab8a950aaf6a0` |
| GPU | `84b881e8129774acee3e4faf944e833c407711fd` |
| HAL | `9c1cd8dfff33478e32668c5cd181dd094ec2881b` |
| APLS | `ddd6743083e67c2fbfd57bb1c2724e932b2633c4` |

The six changed modules and the parent integration are committed on
`codex/arm64e-boot-metal`; HAL retains its existing published commit. Remote
publication is pending explicit user approval under AGENTS.md section 7.
`fresh-integration.json` records a fresh recursive clone using local committed
objects with temporary URL mappings. It does not assert remote reachability.

## Execution evidence

- Original macOS 27 M1 kernel collection: 121,864,192 bytes and 342 members
  staged with readback and unchanged SHA. A deliberately incomplete SPTM-prefix
  diagnostic executed four original ARM instructions in x86 EFI, producing three
  native blocks before an unsupported system-register operation. Boot arguments
  were not dereferenced. Detailed original-input traces remain private.
- ARM64/ARM64e authored firmware: native JIT, software PAC/AUT and sixteen GOP
  pixels read back correctly. Nine ordinary/rejection cases plus three explicit
  register/budget/feature-gate cases passed from the fresh integration clone.
- Native JIT assertions: 84 existing, 34 boot/result, 17 PAC and 827 arithmetic/
  conditional-branch assertions passed. The no_std reference runtime tests and
  legacy x86 EFI link/audit also passed.
- Actual AMD Radeon RX 6800 XT: Windows execution of the WSL-built Vulkan
  acceptance example completed six dispatches and 1,280 internal value comparisons,
  using three pipeline compilations. No CPU fallback. Public outputs and source
  hashes are in the GPU module's `validation/windows-rx6800xt-20260908/` directory.
- Fresh workspace: 434 Rust tests passed with one optional image-copy test ignored;
  that test was subsequently run against the actual 169,472-byte default NXARMJIT
  image and passed. Python ran 132 tests, passed 131, and skipped one environment
  dependent case. All 17 workflow YAML files parsed successfully. Host and EFI Clippy checks
  completed successfully with non-fatal warnings surfaced, matching CI policy.

## Remaining boot and Metal work

The original trace uses the explicit `unprovisioned-sptm-prefix` diagnostic ABI.
It supplies no SPTM argument block or services and no resolved runtime platform
DeviceTree. Further system-register support, translated memory/MMU behavior,
SPTM integration, platform devices and sustained XNU initialization remain.
Original restore DeviceTree templates require resolution before runtime use.

The default EFI image still stages inputs and reports missing providers. GOP
readback and native Windows Vulkan compute do not establish a macOS Metal driver
path. Installed macOS boot, userspace and guest Metal are not complete or verified.

Original KernelCache, DeviceTree and iBoot members were downloaded from Apple's
macOS 27 restore archive and verified individually; the entire 22.7 GB IPSW is
still downloading and has not yet passed its full-file SHA256 check. All original
inputs remain outside public commits under `_isolated/`.

## Reproduce

After the development branches are published:

```sh
git clone --recurse-submodules --branch codex/arm64e-boot-metal https://github.com/26x86/26x86.git
cd 26x86
python3 Tools/verify_nextcore_submodules.py --cargo --require-clean
cargo test --locked --manifest-path nextcore/Cargo.toml --workspace
cargo build --locked --manifest-path nextcore/Cargo.toml -p nextcore-efi --release \
  --target x86_64-unknown-uefi --features arm-jit --bin NXARMJIT
```

Firmware details and exact harness commands: `../arm-efi-20260908/results.md`.
The original trace's private coordinates are intentionally not reproduced here.
The startup distinction follows the public XNU
[startup source](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s).
