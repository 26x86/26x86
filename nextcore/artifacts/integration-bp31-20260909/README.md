# BP31 integration evidence

Fresh recursive baseline8bcf5c528695243c10df9a3d148d21a90b46cb90 passes476
workspace,149 Python,25 GUI and93 reference tests;78 authored x86 EFI cases
and6 separate CLI rejections;3,668 conditional Arm oracle cases and158 exact
fault comparisons; native/PAC/scalar/pair/provider/ABI, Vulkan, compiled firmware
packaging and Clippy. The native conditional matrix contains34,264 cases and
137,070 assertions. Module ISE and EFI PR5s are merged and completed branches
were deleted after clean-state and ancestry checks.

The baseline conditional runner checks arithmetic, preserved state, PC, retirement
and native execution. Follow-up sourcef38a2c30 explicitly requires Rust callback
observations in CI. Its separate strict-provider proof uses the already-built
canonical standalone EFI7495633: all13 conditional cases have exact fetch/native
counts and no data access, and one real direct execution is rejected only for
missing provider evidence. Correct arithmetic is preserved in that negative case;
--negative-control selects one NV fixture and does not mutate the native emitter.
These14 executions are separate from the baseline78, with separate binary hashes.

The final CI uses the strengthened runner against newly built integrated EFI.
The final evidence/documentation head also receives a canonical GitHub recursive
clone, source/inventory/manifest hash checks and final-head CI before merge.
report.json preserves each local baseline command, exit status and duration.
Standalone module reports and strict-provider receipts preserve their own inputs.
Historical base-plus-patch EFI and original aggregate diagnostics remain in the
separate arm-conditional-compare-20260909 bundle; they are not relabeled as this
integration binary. All serial logs here are authored tests, not original images.

The4,096-instruction original diagnostic is a metadata-traversal budget checkpoint.
Native M=1 execution, complete normal startup providers/ABI, usable macOS boot and
guest Metal remain incomplete in this BP31 source.
