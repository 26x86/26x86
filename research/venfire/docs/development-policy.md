# Development host exception and release policy

This policy applies to 26x86's user-space host authorization and its generated
build artifacts. It does not change guest CPU semantics or establish macOS boot
support.

Normal releases require a 64-bit Intel host process with OS-available AVX2 and
best-effort physical Apple hardware evidence. Darwin uses sysctl, IORegistry and
AppleSMC evidence. Linux uses each observed processor's cpuinfo vendor/features,
Apple DMI system and board identifiers, and a bound `applesmc` platform device.
Missing required evidence and known virtualization cause normal authorization to
fail. A Linux live image must therefore include a working `applesmc` driver for
normal Intel Mac authorization; the detector does not load drivers itself.

An isolated lab build may generate `venfire/_build_profile.py` containing exactly
`BUILD_PROFILE = "developer-nonredistributable"`. It must also carry an obvious
`NONREDISTRIBUTABLE DEVELOPMENT ARTIFACT` label in its build metadata, generated
USB/image identity, and runtime evidence. The source tree and ordinary installed
package default to the `release` profile if this generated marker is absent.
An invalid marker fails closed. Environment variables do not select this profile.

The caller must explicitly pass `--developer-host-bypass` for each lab host
authorization. The flag is rejected by a release profile. A developer build
without the flag still applies normal host requirements. The flag permits a
non-Apple machine, Windows host, or known VM for lab work; it never waives Intel,
64-bit x86, or AVX2 requirements. It does not waive immutable input checks,
signature checks, PAC semantics, guest provenance policy, or other trust checks.
It does not modify macOS files or enable boot-chain signature bypasses.

Windows CPU evidence is read using the processor registry vendor and documented
`IsProcessorFeaturePresent(PF_AVX2_INSTRUCTIONS_AVAILABLE)` API. Windows remains
ineligible under normal release policy. Linux AVX2 must be exposed in every
observed processor record; merely advertising a machine model is insufficient.
See [Microsoft's processor feature API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-isprocessorfeaturepresent)
and the [Linux x86 feature flag documentation](https://docs.kernel.org/arch/x86/cpuinfo.html).
Linux Apple's SMC evidence uses the [upstream Intel applesmc platform driver](https://github.com/torvalds/linux/blob/master/drivers/hwmon/applesmc.c).

Project-controlled normal release packaging must reject a developer build before
creating distribution outputs. `policy.require_release_build()` provides the
runtime-side check; package/image build entry points must also validate the
source/staging profile so copying a marked developer tree cannot silently become
a normal release. Developer lab images stay distinct from release artifacts.

“Nonredistributable” here is the project's labeling, release-process and support
policy for its development artifacts. It is not an additional restriction on
upstream GPL or other open-source license grants. Upstream license terms remain
unchanged, and required notices/source obligations still apply. This mechanism
does not claim to prevent independent forks, source edits, privileged host
spoofing, or removal of the project policy. Hardware checks remain best-effort
evidence, not cryptographic physical-Mac attestation.
