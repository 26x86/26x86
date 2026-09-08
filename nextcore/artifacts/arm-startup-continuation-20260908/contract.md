# Original startup continuation and firmware DT contract — BP26

Current: the original macOS 27 kernel prefix retires four instructions in x86
EFI before an unsupported standard thread-pointer system register. The original
firmware device tree contains flagged template values and cannot be treated as
the final XNU runtime device tree. The previous source and receipts are retained.

Wanted: implement standard thread/context registers in the delegated CPU scope,
observe the next original boundary using the existing explicit eight-instruction
cold-entry diagnostic, and represent firmware DT templates without inventing
their values. This scope is explicitly delegated by the root agent under BP26.

Decisions:

- CPU agent owns standard TPIDR register and native/reference state semantics.
  EFI/Core agent rebuilds the same x86 EFI JIT path and retains original input
  hashes, registers, instruction word and actual stop point in private receipts.
  The existing `unprovisioned-sptm-prefix` contract remains in force. No SPTM
  arguments/services are fabricated; a budget extension requires an explicit
  documented diagnostic purpose and bounds.
- An independent seven-instruction EFI fixture writes/reads the three standard
  TPIDR registers at EL1 using the nonzero staged-argument address. Equality of
  final x0/x1/x2/x3 and actual native retirement establishes EFI state persistence.
- A new Core `firmware_dt` structural parser is distinct from `flat_dt`. It
  reads node counts and 32-byte property names, treats bit31 of the length as
  `Template`, and uses only the lower31 bits for bounded payload traversal.
  The original length, value and alignment bytes remain borrowed unchanged.
- Bound input bytes, node/property counts and depth before allocations; reject
  truncation, arithmetic overflow, invalid names and trailing input. Template
  bodies remain opaque bytes, with an optional checked ASCII C-string view.
  There is no expression interpreter, evaluation, masked runtime serialization
  or property-value substitution.
- Runtime conversion first rejects any unresolved template, then delegates to
  the existing strict `flat_dt` validator. A structural firmware parse is not
  evidence of runtime-device-tree completeness or validity.
- The EFI trace caller uses this distinction before placement: unresolved
  template input yields an explicit count and UNSUPPORTED before TRACE_ENTER.
  Validated unflagged bytes remain a diagnostic tree with platform_complete=false.
- Tests use independently authored trees with literal/template distinctions,
  exact source preservation, malformed count/length/name/depth bounds and strict
  runtime rejection. Original firmware inspection produces count-only public
  outcomes; raw template strings and original bytes remain `_isolated`.

Primary public references (read 2026-09-08):

- m1n1 firmware ADT framing and explicit template flag/type handling:
  https://github.com/AsahiLinux/m1n1/blob/main/proxyclient/m1n1/adt.py
- XNU runtime DT traversal consumes the complete runtime property length:
  https://github.com/apple-oss-distributions/xnu/blob/main/pexpert/gen/device_tree.c
- XNU public SPTM cold-entry convention:
  https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/arm64/sptm/start_sptm.s

OPEN_QUESTION: The providers and exact target protocol that resolve the original
firmware DT templates into a complete runtime M1 DT remain unimplemented.
