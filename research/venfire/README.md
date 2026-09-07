# 26x86-VenFire

Standalone user-space research and conformance layer for the 26x86 project.
The package owns ARM64 guest conformance, input-integrity checks, recovery and
storage policy, host evidence, and the reviewed QEMU patch provenance. It is
intended to be published as `NiSeullent/26x86-VenFire`; the core OpenCore/EFI
repository remains `NiSeullent/26x86`.

The portable execution layer is:

```text
x86_64 Linux/WSL host -> QEMU TCG -> VMApple device model -> AArch64 guest
```

No Virtualization.framework, HVF, Apple CPU, or Apple hardware is required for
the emulator path. This is a host-emulation property, not evidence that a
caller-supplied macOS Golden Gate bundle has booted.

Legacy Linux/QEMU experiments keep their AVX2 and private-build restrictions;
they do not define the SSE4.1/SSE4.2 requirement of the native EFI engine.
Recorded Monterey execution cannot be treated as macOS 26/27 AIC/iBoot proof.

First-party integration follows the repository license. QEMU patch derivations
retain upstream QEMU copyright and license terms; graphics dependencies retain
their respective licenses. Apple assets, guest disks and personalized tickets
are not included.

`venfire/conformance.py` runs only the self-authored guest in this repository.
Its PASS result proves synthetic AArch64/EL1/device execution. The macOS boot
evidence gate remains false until a caller supplies an original signed
Golden Gate firmware/storage bundle and the UART observer sees target-matching
XNU and userspace markers.
