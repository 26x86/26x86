# QEMU patch provenance

- Repository: <https://github.com/qemu/qemu>
- Base commit: `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`
- Series: `series`
- `0001-vmapple-explicit-tcg-research.patch` exposes an explicit TCG/headless
  mode and removes only the HVF/PV-graphics build gates required for it.
- `0002-vmapple-block-barrier.patch` preserves the guest-visible storage
  barrier boundary used by the COW runner.
- `0003-vmapple-recovery-usb.patch` adds the bounded recovery transport used by
  the research-only path.
- `0004-vmapple-bdif-cow-write.patch` adds the explicit BDIF write gate and
  overlay-safe write path. It is off by default.
- `0005-vmapple-iboot-firmware-window.patch` expands the research firmware
  window to accept the decoded j274 Stage2 image.
- `0006-vmapple-tcg-enable-el2.patch` enables EL2 only for the explicit TCG
  research profile.
- `0007-vmapple-j274-impdef-and-highram.patch` adds the opt-in j274
  implementation-defined register subset, a high-RAM alias for observed
  Stage2 relocation, and the `research-graphics` selection boundary.
- `0008-vmapple-stage2-el1-pauth-reset.patch` keeps the Stage2 research
  profile's initial firmware entry at non-secure EL1, then exposes EL2 only
  for the later handoff and permits the observed EL1 counter/PAuth accesses.
- The AES change in patch 0001 only makes a debug hexdump array bound an enum
  constant for GCC C compatibility; virtual AES key slots and operations are
  unchanged.
- License: GPL-2.0-or-later, matching the modified upstream files.

Apply from a clean checkout of the exact base:

```text
while read -r patch; do
  test -z "$patch" || git apply --check "patches/$patch"
  test -z "$patch" || git apply "patches/$patch"
done < patches/series
```

Run `tools/backend_audit.py --source PATH_TO_QEMU --require-patched` afterward.
The output records the current patch SHA-256 and rejects extra source changes.
See `docs/backend.md` for behavior, validation, and unresolved requirements.

This patch enables an explicit TCG/headless research path. It neither patches
macOS nor claims that macOS boots. No fabricated DCO sign-off is attached.

The optional Reims graphics candidate under `patches/graphics/` deliberately
uses its own frozen `core-series` (0001 through 0004). It is a synthetic host
graphics acceptance line and must not be confused with raw j274 Stage2 or
guest WindowServer evidence.

0009 adds an explicitly-unavailable optional-RPC diagnostic window at 0x004fc000 (guest-ram linked, preserves guest bytes, synthesizes no success/result/signature state). It is a delta on top of 0001-0008 and must not revert the 0005 firmware window, 0006 EL2/PAuth path, or graphics research options.

