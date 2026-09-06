# QEMU patch provenance

- Repository: <https://github.com/qemu/qemu>
- Base commit: `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`
- Patch: `0001-vmapple-explicit-tcg-research.patch`
- Modified scope: `configs/devices/aarch64-softmmu/default.mak`,
  `hw/vmapple/Kconfig`, `hw/vmapple/vmapple.c`, `hw/vmapple/aes.c`
- The AES change only makes a debug hexdump array bound an enum constant
  for GCC C compatibility; virtual AES key slots and operations are unchanged.
- License: GPL-2.0-or-later, matching the modified upstream files.

Apply from a clean checkout of the exact base:

```text
git apply --check PATH_TO_PATCH
git apply PATH_TO_PATCH
```

Run `tools/backend_audit.py --source PATH_TO_QEMU --require-patched` afterward.
The output records the current patch SHA-256 and rejects extra source changes.
See `docs/backend.md` for behavior, validation, and unresolved requirements.

This patch enables an explicit TCG/headless research path. It neither patches
macOS nor claims that macOS boots. No fabricated DCO sign-off is attached.
