# New ERET-entry fetch oracle

New authored subset, not an edit to frozen428/440-case observations:74 corresponding fault cases plus4 valid RET controls. First case is moved to the front for the negative control. EL2 ERET enters the EL1 target directly with SPSR_EL2=0x3c5. For EL0, EL2 enters a helper and EL1 ERET enters the target with SPSR_EL1=0x3c0. Both values set BTYPE=0. X30 points to the authored SVC completion label. Actual saved BTYPE is checked for every exception/completion.

Descriptor construction retains original authored source expressions; the new build has separate actual addresses, ELF hashes and captured controls. No request PSTATE masking. The negative binary aligns the first target address so its normally expected PC alignment exception must disappear. This does not reuse the original A0 negative control. The12 known QEMU PC-priority contradictions remain separately preserved and excluded.
