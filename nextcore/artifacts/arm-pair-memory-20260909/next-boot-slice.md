# Next native address-space slice

Current state: the native C JIT explicitly rejects SCTLR.M. The reference walker
has independently checked 4 KiB/16 KiB translation, address-size and permission
semantics, but its existence does not make generated native fetch/load/store
use those semantics. BP28 fixes general integer pairs and advances a bounded
diagnostic. The exact macOS27/M1 normal handoff ABI is still unproven.

Wanted next slice: connect a **fixed, explicitly selected EL1 stage-1 16 KiB
address space** to native instruction fetch and the currently supported integer
RAM accesses. Use nonidentity virtual-to-physical mappings and the existing
reviewed walker behind a single checked bus contract. This is independently
useful to either eventual SPTM or non-SPTM boot and requires no guessed bootstrap
structure. Root/CPU agreement on API and ownership is required before code.

## Bounded implementation contract

1. Keep the existing no-provider/MMU-on rejection as the default. The new
   diagnostic entry must supply a supported TCR/TTBR/SCTLR configuration and an
   explicit physical RAM provider. Configure failure preserves all prior state.
2. Start with an immutable translation regime for one bounded run. Fetch uses
   guest VA and execute permissions; load/store use data VA and read/write
   permissions. Underlying host pointers are obtained only after physical RAM
   bounds checks. The code cache must identify the address-space generation and
   must not reuse a block fetched under another mapping or execute permission.
3. Route instruction fetch and existing single/pair RAM operations through the
   same address-space contract. For crossing accesses, preflight every required
   page and both pair elements before store or writeback. Preserve guest fault
   PC, syndrome, destination registers and precise retired count.
4. Changes to translation controls, unsupported TLBI, unsupported device memory,
   unsupported granules or wider regimes stop with an explicit diagnostic
   outcome. Do not silently use identity addressing or claim live TLB support.
   A later generation-invalidation slice enables mutable mappings and TLBI.
5. A high guest VA is not a host function pointer. Only validated ARM bytes are
   translated into x86 blocks. ARM guest page permissions and host W^X remain
   independent requirements.

## Independent acceptance

Use authored AArch64 payloads and page tables, with a separately assembled
AArch64/QEMU oracle for architectural outcomes and actual x86 OVMF execution
for native integration. Compare semantic result fields, not host timing or
host pointer values. Include at least these distinct cases:

| Case | Required observable result |
| --- | --- |
| TTBR1 high-VA fetch mapped to nonzero physical RAM | Native execution reaches an authored marker; identity mapping cannot explain success |
| Separate data VA mapped to another RAM page | Integer loads/stores and pairs read back expected values; W results zero-extend and SP returns exactly |
| Unmapped instruction page | Instruction abort before any instruction from that page retires |
| Executable/read-only page used for a store | Permission abort with unchanged memory and registers |
| Read/write non-executable page used for fetch | Execute permission failure; a previously compiled block cannot bypass it |
| Pair crossing into an unmapped or protected page | No partial store and no writeback; exact fault class and retirement boundary |
| Valid then invalid configuration | Failed configuration preserves earlier accepted state, independently checked before any run |
| Two separately initialized sessions mapping one VA differently | The second session observes its own mapping, exposing stale code-cache reuse |

The reference and native paths must agree with the independent architectural
oracle on supported cases. A changed-permission/table negative control must
make the test fail. Keep the selected no-LPA2 descriptor restrictions, including
reserved 16 KiB L1 blocks, and partial root-index/canonical VA rules already
covered by the independent walker tests. No original kernel is required for
this acceptance stage. Only then authorize a separate bounded original replay.

## SPTM remains a versioned provider question

Public XNU's SPTM entry consumes an SPTM-produced bootstrap structure containing
live mappings and shared state. It performs fixups before a real service changes
page permissions. This is not satisfied by zero-filled argument storage or a
success-returning stub. [Public XNU SPTM entry](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sptm/start_sptm.s),
[SPTM startup consumer](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/osfmk/arm64/sptm/arm_init_sptm.c).

The inspected public SDK layouts differ across releases and have no stable
leading bootstrap-version discriminator. Those headers currently have pinned
public-mirror provenance, not verification against an original Apple SDK
package. Their layouts must not be selected automatically as the macOS27/M1
ABI. [Apple SDK header mirror, 15.5](https://github.com/alexey-lysiuk/macos-sdk/blob/896cd40df984b847d486723edce50e247385617e/MacOSX15.5.sdk/System/Library/Frameworks/Kernel.framework/Versions/A/Headers/platform/sptm/sptm_xnu.h),
[26.5](https://github.com/alexey-lysiuk/macos-sdk/blob/896cd40df984b847d486723edce50e247385617e/MacOSX26.5.sdk/System/Library/Frameworks/Kernel.framework/Versions/A/Headers/platform/sptm/sptm_xnu.h).

Retain the outer collection entry: Apple's collection builder deliberately
copies the kernel thread command and slides its PC into the collection. A
different embedded thread PC alone is not evidence of an alternate boot path.
[Apple collection builder](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/kernel-collection-builder/AppCacheBuilder.cpp#L4843).

OPEN_QUESTION: Confirm the target-specific handoff family, initial translation
regime and firmware-produced state before connecting any production SPTM
encoder or service. Native address-space acceptance is progress toward that
work, not evidence that the unknown target ABI has been resolved.
