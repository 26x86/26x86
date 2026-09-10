# T2 Mac Notes

Specific guidance for running 26x86 on Intel Macintosh systems equipped with the Apple **T2** Security Chip.

## System Integrity Protection (SIP)

- Booting OpenCorePkg on T2 Macs may configure SIP to `0xFFF` (effective full disablement) to accommodate pre-boot security handoffs.
- In certain hardware revisions, thermal management or throttling workarounds require disabled SIP states.
- For maximum security, enable SIP as soon as initial setup and validation are complete: `csrutil enable`.

## BridgeOS & Firmware Pairing

- T2 Mac hardware requires tight synchronization between macOS and BridgeOS on the T2 chip.
- Applying major OS updates without corresponding BridgeOS updates can cause boot loops or recovery failures.
- Always perform a full Time Machine or clone backup prior to updating.

## Hardware Acceleration & Audio

- Built-in audio controllers on T2 models (MacBookPro15,x, MacBookPro16,x, iMac20,x) depend on T2 bridge routing.
- Verify AppleAudio and ambient sensor operation in the validation matrix: see [Known-Issues.md](./Known-Issues.md).
