# iBoot (AArch64) Personality Scope

This specification locks policy constraints across the **userspace configuration validation tier** and the **VMApple recovery execution tier**.

## Scope & Policy Gates

1. **Target Operating System:** Exclusively macOS guests (`GuestOS = macOS`). Mobile operating systems (iOS, iPadOS, watchOS, tvOS) are strictly prohibited and rejected during input validation.
2. **Machine Architecture:** MachineType is fixed to `iBoot(AArch64)`.
3. **Recovery Media:** Standardized on `DFU/IPSW` protocols targeting `_default.ipsw`.
4. **Execution Boundaries:** Simulated execution in QEMU TCG models does not assert native macOS boot claims without empirical UART markers.
