# Troubleshooting by evidence layer

Start with the first layer that fails and avoid changing unrelated layers at
the same time.

| Symptom | First layer to inspect |
| --- | --- |
| Invalid plist or missing entry | OpenCore configuration and package tree |
| EFI does not appear | Firmware mode, ESP layout, and boot entry |
| Boot picker appears but macOS fails | Boot arguments, kext set, and target model |
| Progress bar reaches black screen | GPU/output path and WindowServer evidence |
| Hardware works only partially | USB, audio, touch, sleep, and device-specific logs |

Static checks narrow the search; they do not replace physical acceptance. Keep
the working display and boot path intact while testing one variable at a time.
