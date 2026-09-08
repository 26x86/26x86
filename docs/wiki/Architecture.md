# Public architecture

```text
NextCore application
    -> configuration and EFI preparation
    -> target-specific validation
    -> physical or emulated acceptance evidence

NextCore public modules
    -> configuration and format contracts
    -> EFI handoff contracts
    -> runtime and hardware-abstraction experiments
```

NextCore is the product name for the application and independent clean-room EFI
boot engineering. The firmware picker selects explicitly configured EFI
applications on its current volume. Public kernel-format codecs and HAL/GPU
modules support the Tahoe and Golden Gate development paths. External OpenCore
components remain attributed where the integration and reference paths use them;
they are not renamed as our own implementation.

The current native EFI path reaches Tahoe Recovery and Terminal through the
original operating-system booter. Direct kernel-collection entry and Golden Gate
ARM64E execution remain incomplete. Host Vulkan compute has run on the Intel GPU;
the actual Recovery Metal probe reports no device. Full guest acceleration is a
separate required result. These observations use local QEMU/OVMF and do not prove
physical-Mac compatibility.

The architecture is evidence-first: each layer can report only what it
actually measured. A successful build or file check cannot promote an
unverified firmware, kernel, graphics, or physical-hardware claim.
