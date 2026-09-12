# Development environment setup

**Current Status:** Source, application and firmware setup; no OS installation is performed.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

Use this guide to obtain the source and run read-only checks. It does not install
macOS or certify a hardware target. Start with [compatibility](compatibility.md)
and [current progress](progress.md).

## Clone the integration and exact modules

```bash
git clone --recurse-submodules https://github.com/26x86/26x86.git
cd 26x86
git submodule sync --recursive
git submodule update --init --recursive
python3 Tools/verify_nextcore_submodules.py
```

Keep the submodules at the integration's recorded commits. Separate sibling
copies of the seven crates do not replace these gitlinks. See
[Module repositories](wiki/Nextcore-Modules.md) for ownership and publication.

## Python application inspection

Use a supported Python installation for the selected checkout and install its
platform-marked requirements in a virtual environment. Optional GUI dependencies
and native packaging tools are distinct from the Rust firmware toolchain.

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m x86 --help
python -m x86 detect --json
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m x86 --help
.\.venv\Scripts\python.exe -m x86 detect --json
```

The explicit Windows interpreter path avoids dependence on shell activation.
Use `python -m x86 wizard` when the selected GUI backend and its platform runtime
are installed. A working wizard or detector is application evidence only.

## Rust firmware development

On Windows, use WSL2 for the Linux/x86 native proof tools. A Linux filesystem
build directory avoids cross-filesystem build overhead. The firmware build uses
Rust, Clang/LLD and LLVM tools; actual firmware tests additionally use QEMU/OVMF.
Check the selected module's toolchain and CI rather than assuming a historical
compiler version is mandatory.

```bash
rustup target add x86_64-unknown-uefi
cargo test --manifest-path nextcore/Cargo.toml --workspace
cargo build --locked --manifest-path nextcore/Cargo.toml -p nextcore-efi   --release --target x86_64-unknown-uefi --features arm-jit --bin NXARMJIT
```

`NXARMJIT` normal entry reports missing providers. Authored probe features and
bounded original-input diagnostics have separate selectors and acceptance
criteria; do not enable them as a substitute for normal boot readiness.

## Host and deployment boundaries

Windows/Linux tools can inspect configuration and build developer artifacts.
macOS live root-patching and service installation require their actual supported
host and preflight. Building EFI bytes on a host does not prove that a machine
can boot them. QEMU/OVMF is a development firmware environment, not physical
hardware acceptance.

Before any disk deployment, identify the current ESP and target disk, preserve
a complete backup and test external media. Use [installation boundaries](wiki/Installation-Notes.md)
and [troubleshooting](wiki/Troubleshooting.md). No command above modifies a disk
partition or performs an OS upgrade.

## Documentation build

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs build --strict
```

A successful site build checks documentation structure, not runtime support.
See [Build and development](wiki/Build-and-Development.md) for change validation.
