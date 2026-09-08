# BP29 bounded original scalar-prefix diagnostic

Current: the corrected BP28 diagnostic executed47 instructions in10 native x86
blocks and stopped at an unsigned-immediate32-bit load. Root delegates one new
diagnostic with the independently verified scalar EFI binary built from ISE
8b09f8764f13838baf71c1676575cb829bcd7902. No source/module/Git changes are made.

Use the existing immutable original input and diagnostic DT, unchanged physical
placement and outer collection entry, explicit nextcore-irq-compat-v1 software
profile, and the same incomplete SPTM convention. The maximum instruction
budget remains64. Reaching it is a budget outcome, not proof of a next missing
instruction. Any larger budget needs a new documented scope decision.

Verify the validated EFI SHA256 and authored scalar proof before execution.
Preserve old receipts, record a fresh private command and input/source/binary
hashes, and compare original and ESP copy hashes after the run. Original bytes,
coordinates and detailed traces remain private. Only aggregate counters,
generic outcome, source identity, method and remaining prerequisites appear
in the public result. Do not infer normal startup, SPTM, native MMU or Metal.
