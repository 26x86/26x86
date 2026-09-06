# AIC device layer

The initial first-party model covers AIC v1 wired interrupt routing. Register
facts are checked against the [Asahi Linux AIC driver](https://github.com/AsahiLinux/linux/blob/asahi/drivers/irqchip/irq-apple-aic.c):
INFO 0x0004, WHOAMI 0x2000, EVENT 0x2004, TARGET_CPU 0x3000. The v1 maximum
register layout spans 1024 sources; software-set/clear, mask-set/clear and
hardware-state banks follow the target array at 128-byte strides.

Acknowledgment masks the delivered IRQ. An asserted level is delivered again
after unmasking. CPU affinity and lowest-numbered priority are implemented.
Software pending and physical level are independent. Unknown MMIO, invalid
widths and out-of-range targets fail explicitly.

IPI, FIQ, Apple timer system registers, AIC2/3 and privileged CPU exception
delivery remain incomplete. The model is not yet sufficient to boot iBoot or
macOS. No GIC model is substituted. The scheduler must serialize model accesses.
MMIO base address and virtual device wiring belong in config.plist Hardware;
no physical Apple address or guest device-tree identity is invented here.
