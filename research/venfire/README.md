# 26x86 platform research

Imported platform, original-asset integrity, personalization, device and CPU
verification work. The Python namespace `venfire` and historic evidence are
retained for reproducibility. This directory is not the Apple Silicon Sandbox
runtime. The product runtime is `sandbox/efi`, invoked by OpenCore.

Legacy Linux/QEMU experiments keep their AVX2 and private-build restrictions;
they do not define the SSE4.1/SSE4.2 requirement of the native EFI engine.
Recorded Monterey execution cannot be treated as macOS 26/27 AIC/iBoot proof.

First-party integration follows the root LICENSE.txt. QEMU patch derivations
retain upstream QEMU copyright and license terms; graphics dependencies retain
their respective licenses. Apple assets, guest disks and personalized tickets
are not included.
