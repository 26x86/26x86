# Target entry audit: diagnostic provenance versus cold handoff

Current Status: r29 executes the selected outer fileset entry under an explicitly
software-defined mapped profile. Target-specific cold-entry ABI, SPTM applicability,
platform provisioning, normal startup and physical macOS remain unverified.

Target State: bind the selected target's actual entry role and required initial
state to matching authoritative evidence, then provide that state and services
through standard UEFI on the physical host.

## Confirmed evidence and limits

| Question | Confirmed observation | What it does not establish |
|---|---|---|
| Which image entry is selected? | Existing metadata identifies exactly one outer ARM LC_UNIXTHREAD PC. Core's staged offset matches it; outer and kernel-member PCs differ. The r29 mapped entry equals the original outer virtual PC after the staging PA-to-high-alias conversion. | No evidence justifies substituting the member PC, minimum image address, or a nearby symbol. Image entry is not automatically a processor's hardware reset vector. |
| Is it executable/file-backed? | The outer PC is in a file-backed executable `__TEXT_BOOT_EXEC` segment in both outer and member segment views. | The segment name alone does not authenticate a specific source function, SPTM ABI, startup reason or initial register values. |
| Does the implementation use that metadata? | Four independently authored EFI canary cases previously distinguished outer, member and image-base entry choices with one-field fixture changes. | Those canaries verify the loader's selection behavior, not this original image's ABI. |
| What is the target identity? | Manifest version/build are 27.0/26A5425a. The kernel-member LC_SOURCE_VERSION is 13432.1.9; the outer image has no LC_SOURCE_VERSION. Outer and member each contain one LC_UUID. UUID values remain isolated. | A source-version field and UUID are matching keys, not proof of a particular public source tree or ABI. |
| What public XNU was compared? | Apple commit `ac9718fb1af618d5ce8678d0dc6e8a58f252216f` identifies its import as xnu-12377.121.6. Its legacy and SPTM startup sources were acquired together and opened. | 13432.1.9 and 12377.121.6 are different version identities. This is not proof that their ABIs are incompatible; it is evidence that exact target-source binding is absent. |
| Does the manifest prove SPTM absence? | All three matching j274ap identities have KernelCache roles and no role names containing SPTM/TXM. | Manifest role absence does not prove the selected kernel uses the legacy startup path, nor prove SPTM services unnecessary. |
| What state does r29 actually supply? | The explicit unprovisioned profile supplies x0=0, x1=owned legacy boot-argument storage, x2/x3=0, owned stack, software IRQ profile and 16K Normal-NC mapped aliases. The receipt explicitly marks target ABI unverified. | These values are not captured target reset state. Zero cannot be relabeled a verified cold sentinel, and absent x2 cannot be relabeled valid SPTM arguments. |
| What does r29 prove? | The preserved image executes 42,256,374 instructions and 6,012,373 data operations before an MMFR1 read trap. Provider status is zero. | Instruction count does not prove correct target initialization, completion of all fixups, real platform services, or reaching userspace. |
| What display is observed? | Owned 1280x800 framebuffer RGB matches a zero frame and GOP readback. | This is not original kernel console rendering, ongoing post-firmware presentation or a physical desktop. |

The initial host-staging receipt correctly recorded unresolved placement, entry,
platform and chained-pointer requirements. It predates the later diagnostic
staging/alias work; its old booleans must not be treated as the latest runtime
receipt. Equally, later diagnostic success must not erase target-entry/provider
requirements that the diagnostic explicitly leaves unprovided.

## Public startup contracts, kept separate

The pinned [legacy startup](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/start.s)
branches from its entry trampoline to a cold routine that preserves the incoming
x0 boot-argument pointer and builds the translation environment before returning
to initialization. It distinguishes its entry trampoline from low reset vectors.

The same revision's [SPTM startup](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm64/sptm/start_sptm.s)
documents startup-reason x0, traditional arguments x1 and SPTM arguments x2.
It initially executes in the boot segment, saves the argument pointers, performs
image fixups, installs exception vectors and invokes SPTM fixup completion before
entering the main initialization path. Its public file includes an external
`sptm/sptm_xnu.h`; the selected public tree did not contain that header in the
recursive tree lookup. Symbolic reasons alone do not supply numeric constants
or a complete external argument/service implementation.

The public [legacy fixup caller](https://github.com/apple-oss-distributions/xnu/blob/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk/arm/arm_init.c)
rebases/signs its fileset before consuming the copied arguments. Therefore opaque
chain words are not, alone, evidence that the loader should rewrite them. Existing
chain-membership observations support a fixup-like access pattern but do not bind
the target's containing function to this older public source.

The import identity is independently recorded by the official
[commit metadata](https://github.com/apple-oss-distributions/xnu/commit/ac9718fb1af618d5ce8678d0dc6e8a58f252216f).

## Exact missing evidence

1. A target-matching source/debug-symbol/build identity tying the kernel UUID and
   13432.1.9 version to the selected outer entry and its startup configuration.
2. An authoritative statement or matching target observation of startup reason,
   register roles, pointer address spaces, current exception level, stacks,
   translation state, PAC state and executable-region permissions at that entry.
3. If SPTM is applicable, the actual external argument and dispatch contracts,
   including the required fixup-completion transition. No successful fake service
   reply can substitute for this requirement.
4. Target-consumed DeviceTree/platform, interrupt, timer and storage services,
   followed by firmware exit and sustained framebuffer/input/userspace evidence.

## Next smallest discriminating experiment

The authorized **exact-entry-symbol lookup has completed**. All 6,947 member
symbol records were checked for exact equality to the selected outer entry;
there were **zero exact matches**. Symbol and string-table ranges were validated
inside the member LINKEDIT file range. No symbol names or instructions were
decoded, and no nearest-symbol inference was made. This does not establish that
the entry is unnamed in a full matching debug package; this image's available
symbol table simply does not independently resolve its role.

The next smallest discriminator is a metadata-only UUID/build identity match
against an already available or officially obtained matching KDK/debug-symbol/
source package. The isolated receipt retains both UUIDs and the member version.
Keep original names/coordinates isolated and publish only match/mismatch,
identity provenance and justified contract outcome.

Success requires a matching target identity and evidence identifying the entry
role; an approximate symbol name, neighboring symbol, segment name or older
public source is insufficient. If exact binding remains unavailable, preserve
that result and keep the current run classified as diagnostic. Do not test a
guessed x0/x1 swap or construct unknown SPTM arguments to increase the count.

After binding, a minimal authored entry consumer should assert the selected
contract's register roles, mapped permissions and first required service before
another original run. The acceptance target remains real UEFI-to-installed-macOS
startup on the physical host, not an ever-longer bounded instruction trace.

## Audit scope and integrity

Two bounded metadata passes each read the original file twice for before/after
SHA256: **four original-file read operations total**. The first parsed outer and
kernel-member load commands; the second scanned 6,947 symbol records but decoded
zero symbol names because no record exactly matched the selected entry. UUIDs
and coordinates remain isolated. No instruction was decoded, no image byte was
modified, and no original replay was launched. Existing staging, entry-provenance
and r29 receipts were read; only sanitized relations are included here. The
accompanying JSON records exact input/parser/primary-source hashes.
