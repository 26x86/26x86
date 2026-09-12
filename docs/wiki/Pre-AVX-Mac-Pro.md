# Older Mac Pro CPU capability notes

**Current Status:** CPU capability diagnosis; no universal pre-AVX execution claim.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

A model name does not replace CPU feature detection. MacPro5,1-class Westmere
systems are a pre-AVX context; do not classify every MacPro6,1 as pre-AVX or
pre-AVX2 based on a shared profile name. Record the actual processor and usable
instruction features for the configured operating system.

```bash
python3 -m x86 detect --json
```

Detection and generated boot arguments are preparation evidence. They do not
prove that Safari, WindowServer, the kernel or third-party applications run on
the selected build. Check [compatibility](../compatibility.md) and capture the
actual crash context before choosing a CPU workaround.

`revpatch=jsc` and any selected RestrictEvents build must be evaluated against
that build's public documentation and source. Do not describe them as a general
AVX-to-SSE translator or a universal Safari fix without a matching runtime test.
See [Safari diagnostics](Safari-PreAVX-Fix.md).

A colored display and an illegal-instruction exception are distinct symptoms.
Diagnose each independently; [display tint notes](Mac-Pro-Tahoe-Yellow-Screen.md)
do not establish the cause of a CPU exception.
