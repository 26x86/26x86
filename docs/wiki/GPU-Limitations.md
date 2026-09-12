# Graphics and display limitations

**Current Status:** Firmware/host presentation is separate from persistent guest output and Metal.

**Target State:** Persistent physical guest display first, then separately verified guest acceleration.

No vendor-wide or model-wide NextCore Metal support tier is established.
The [compatibility catalog](../compatibility.md) records hardware targets and
actual evidence separately. A GPU appearing in a profile is not proof that its
macOS driver initializes on the requested build.

## Separate the four paths

| Path | Current interpretation |
| --- | --- |
| EFI GOP/text console | Boot-services presentation; does not establish guest scanout |
| Host Vulkan tests | Host backend execution for the named adapter and driver |
| Guest framebuffer | Requires a persistent guest mapping and visible presentation |
| Guest Metal | Requires guest device creation, commands, fences and readback |

The active macOS 27 milestone prioritizes a visible, interactive physical guest
desktop before acceleration. Persistent framebuffer ownership/presentation and
post-firmware display lifetime remain incomplete. A small post-run GOP blit is
only a firmware probe. The recorded Tahoe Recovery Metal probe found no device.

AMD, Intel and NVIDIA are implementation targets. Polaris, Vega, Navi, Intel
integrated graphics and legacy NVIDIA names must not be described here as
universally accelerated on Tahoe or Golden Gate without matching receipts.
Mellow's current diagnostic artifact also does not supply a working guest Metal
driver; see [Mellow](../MELLOW_INTEGRATION.md).

For a black screen, preserve the working boot route and identify whether EFI,
XNU, userspace or the display path stopped first. See [Troubleshooting](Troubleshooting.md).
