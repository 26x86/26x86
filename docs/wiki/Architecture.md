# Public architecture

```text
26x86 workflow
    -> OpenCore configuration and EFI preparation
    -> target-specific validation
    -> physical or emulated acceptance evidence

Nextcore public modules
    -> configuration and format contracts
    -> EFI handoff contracts
    -> runtime and hardware-abstraction experiments
```

26x86 is the user-facing patcher and integration layer. OpenCore remains the
public bootloader integration surface. Nextcore is documented as an independent
clean-room implementation and contract family; it does not depend on private
Apple source or private research assets.

The architecture is evidence-first: each layer can report only what it
actually measured. A successful build or file check cannot promote an
unverified firmware, kernel, graphics, or physical-hardware claim.
