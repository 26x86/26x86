# Safari 26 Pre-AVX Instruction Fix

Safari 26.6.1 WebContent executes AVX instructions (`vmovaps`) on pre-AVX Intel CPUs, resulting in `EXC_BAD_INSTRUCTION` / `SIGILL` crashes.

## How the Fix Operates

- Even when the standard RestrictEvents parameter `revpatch=jsc` masks JavaScriptCore AVX feature flags, Safari 26.6.1 includes probe routines (such as `ctiMasmProbeTrampoline`) that directly issue AVX opcodes without feature checking.
- The 26x86 RestrictEvents build intercepts this instruction sequence and translates it to the equivalent legacy SSE `movaps` instruction.
- **No direct modification of the system volume or root filesystem is required.** 26x86 handles this entirely at boot time: it substitutes `RestrictEvents.kext` in the EFI partition and automatically appends `revpatch=jsc` to `boot-args`.

## Verification Steps

1. Launch Safari on macOS 26 Tahoe on a MacPro5,1.
2. Navigate to JavaScript-intensive sites (e.g. WebGL demos, complex web applications).
3. Confirm in Console.app that `com.apple.WebKit.WebContent` does not crash with `SIGILL (ILL_ILLOPC)`.
