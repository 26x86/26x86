# BP30 opt-in tiered diagnostic contract

The immutable scalar runtime's previous original-input diagnostic returned
budget status 5 after exactly 64 retired instructions and 12 native blocks.
Root authorized a separate diagnostic-only extension while BP29 source stayed
frozen. This contract was recorded before source edits.

Only the explicitly delegated Core and EFI worktrees may change. Preserve the
existing parser entry, default profile ceiling of 64 and absent-profile ceiling
of 8. A new entry requires an explicit ceiling selected from 64/256/1024/4096.
Budgets above 64 must also be one of 256/1024/4096 and no greater than the chosen
ceiling. Reject zero, invalid ceilings including 65/4097, unsupported tiers and
absent-profile budgets above 8. Existing valid values at or below 64 retain
their behavior. No default caller gains a larger limit.

Only opt-in EFI feature `arm-jit-tiered-trace` selects ceiling 4096 and prints
an extended-diagnostic marker. It implies the existing probe and trace
features. The host tool requires explicit `--tiered-diagnostic` and verifies
that marker. Builds use a separate workspace and immutable scalar runtime,
with exact source/binary/input digests retained.

Acceptance covers parser boundaries and an independently authored x86 EFI run
that retires exactly 256 instructions with its expected register value. The
default parser/tool/firmware must reject larger budgets. Only after this proof
may unchanged original input run at 256; 1024 and then 4096 are allowed only
when the preceding run returns budget status 5 at the exact requested count.
Stop on any other result. Original bytes and coordinates stay private. A
prefix result supplies no missing SPTM, runtime-DT, native-MMU, normal OS boot
or Metal implementation. Root retains all publication and dependency pins.
