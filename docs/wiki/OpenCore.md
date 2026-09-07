# OpenCore integration

## Scope

OpenCore is the public boot and configuration surface of 26x86. This project
uses OpenCore concepts and public package interfaces for EFI preparation,
device properties, boot arguments, kext loading, and root-patch planning.

The repository does not claim that a generated configuration proves a physical
Mac boot. EFI inspection, `ocvalidate`, emulator output, and runtime hardware
acceptance are separate evidence layers.

## Public workflow

1. Identify the target model, firmware mode, GPU, storage, and current backup.
2. Select the matching OpenCore package and support files.
3. Generate or update the configuration through the guided 26x86 workflow.
4. Validate the file tree and plist before transferring anything to an ESP.
5. Record physical boot, display, acceleration, USB, audio, sleep, and recovery
   results independently.

## Configuration boundaries

Keep OpenCore configuration, public kexts, and public support packages separate
from experimental Nextcore work. Do not mix files from unrelated builds or
present a static plist result as runtime acceptance.

See [Configuration](Configuration.md), [Warnings](Warnings.md), and the
[public/private disclosure boundary](Privacy-and-Disclosure.md).
