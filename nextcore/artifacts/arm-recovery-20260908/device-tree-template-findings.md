# Firmware ADT template versus runtime DeviceTree

Research date: 2026-09-08. No original firmware values or bytes are reproduced.

The published Apple XNU runtime structure defines a 32-bit byte length, and
`next_prop_region` and its bounds checker consume that full length. There is
no template-bit masking in the published runtime consumer:
[Apple DeviceTree structure](https://github.com/apple-oss-distributions/xnu/blob/main/pexpert/pexpert/device_tree.h),
[Apple runtime parser](https://github.com/apple-oss-distributions/xnu/blob/main/pexpert/gen/device_tree.c).

The Asahi m1n1 implementation separately recognizes bit 31 as `is_template`.
Its structural parser uses the low 31 bits for the value extent, parses a
template value as an ASCII C string, and preserves the flag when serializing:
[m1n1 ADT parser](https://github.com/AsahiLinux/m1n1/blob/main/proxyclient/m1n1/adt.py).
This is primary evidence of m1n1's implemented firmware format, not an Apple
ABI promise covering every future firmware release.

The private macOS 27 j274 firmware input was walked without modification:
338 nodes, 4,289 properties, 48 template properties including eight at the
root. All 48 template values satisfy the ASCII C-string shape. The bounded
walk consumed exactly 299,188 bytes and the original SHA-256 stayed unchanged.
The detailed inventory remains in `_isolated`; it is not a public fixture.

The engineering implication is to introduce a distinct firmware-template
reader that preserves template state and reports unresolved properties. A
runtime DeviceTree should be emitted only after required values have actual
providers. Clearing the high bit alone would misrepresent the still-unresolved
template strings as usable hardware data. The current plain runtime codec
should retain its existing length and bounds semantics.

The bounded original instruction-prefix diagnostic uses an explicitly
authored memory-only DeviceTree and does not establish original DeviceTree
handoff, platform initialization or macOS boot completion.
