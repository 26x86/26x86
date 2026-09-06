# USB live host

This layer is **x86_64 UEFI -> Linux initramfs -> 26x86/QEMU userspace**.
Successful USB startup does not establish a macOS boot. The menu and serial
protocol explicitly distinguish those outcomes.

The default image is a GPT disk with one FAT32 EFI System Partition and the removable
loader `EFI/BOOT/BOOTX64.EFI`. GRUB loads the included generic Linux kernel and
RAM filesystem. The live host includes Python, the selected patched QEMU binary
and its dynamic libraries, 26x86, and the self-authored AArch64 conformance
guests. USB/xHCI keyboard and storage, Apple HID, NVMe, SATA and basic framebuffer
dependencies are included when available in the selected kernel. `applesmc` is
included for the central real-Mac host check. The init script uses the absolute
full kmod executable so BusyBox's standalone shell cannot select a modprobe
applet that lacks support for Ubuntu's compressed modules.

The builder creates ordinary image files with mtools. It does not mount an ESP,
use loop devices, write host partitions, install a boot entry, or reboot the
host. By default the live init process mounts only proc, sysfs, devtmpfs, devpts
and tmpfs; logs and guest scratch devices remain in RAM. An optional USB data
partition follows the explicit selection rules below. Internal storage is not
discovered or mounted. No physical USB writing is part of this builder.

Run in Linux/WSL after installing the build dependencies:

```sh
sudo apt-get install linux-image-generic-hwe-24.04 busybox-static grub-efi-amd64-bin grub-common mtools dosfstools kmod
python3 tools/build_usb.py \
  --project /path/to/explicit-build-tree \
  --qemu /path/to/patched/qemu-system-aarch64 \
  --kernel /boot/vmlinuz-7.0.0-31-generic \
  --work /path/to/new/private-build-directory \
  --output /path/to/new/venfire-live.img
```

Use the actual installed kernel filename; the version above is an example.
The project tree must contain an explicit `_build_profile.py`. Release images
never add the Apple-host exception flag. Developer images visibly show
**DEVELOPER BUILD - NOT FOR REDISTRIBUTION**, and add an explicit opt-in to the
kernel command line. The central 26x86 policy still requires Intel vendor and
AVX2. Both image types currently carry `redistributable: false` pending the
project's full source/license release review.

The optional `--restore-helper /path/to/venfire-tss-request` embeds the trusted
native request encoder and the exact dynamic libraries reported by `ldd`,
including their SHA256 hashes. Its private library lookup paths are retained
inside the initramfs. It does not import a signing key or disable certificate
checks. The normal CA bundle is included, and the project's pinned Apple root
certificate stays scoped to `personalization._tss_opener`; it is not added to
the operating system trust store. Helper startup is verified separately from
its ability to encode a valid request or obtain a ticket.

Network configuration is disabled by default. Menu option 6 lists wired
interfaces and requires an explicit interface selection before starting DHCP.
The selected interface's address, default route, and DNS resolver are applied
only to this RAM live host. A DHCP process maintains renewals while the host
runs. Initial lease application has a finite 90-second limit to accommodate
the Python hook under nested TCG; timeout cleanup also stops the hook's process
group. No settings from an installed operating system are read or changed.
Wireless credentials and wireless association are not part of this menu.
The selected kernel's common Intel, Broadcom, Realtek and USB Ethernet modules
and available referenced firmware are bundled; missing modules/firmware are
recorded in the image manifest. This does not establish physical adapter
compatibility before that adapter is tested.

After DHCP, the diagnostic resolves `gs.apple.com`, makes an authenticated HTTPS
GET to the exact TSS endpoint, forbids redirects, and requires a TSS protocol
response. A status such as 93 is recorded as reachability only: this GET does
not request or receive a ticket. Real personalization requires the live guest
identity, current nonces, original restore manifest and component handled by
the separate personalization client. CPU/device diagnostics, DHCP, helper
loading, TSS reachability, ticket issuance and macOS boot remain distinct
results. Network reports and DHCP logs live under `/run/venfire-network-*`.

For an explicit automated network test, build with `--network-autotest` and
optionally `--restore-helper`, then use:

```sh
python3 usb/verify_uefi.py --image /path/to/network-test.img --output /tmp/uefi-net \
  --expect-network --expect-restore-helper
```

This attaches a QEMU user-mode network device; it does not create a host bridge
or alter host interfaces. The startup DHCP behavior is enabled only by the
explicit build flag. The ordinary image continues to wait for menu selection.
For the ordinary image, add `--interactive-network` to the verifier command;
it selects menu 6 and its interface through USB HID, waits for the HTTPS test,
then returns to the host inspection menu. This exercises the explicit UI path
without enabling network configuration on startup.

The visible menu runs the central host policy, then the self-authored AArch64
diagnostic suite, and offers host inspection, repeat diagnostics, an optional
macOS boot probe, a recovery shell and poweroff. An optional
`/opt/venfire/boot-profile.json` must be supplied explicitly to enable the macOS
probe. Missing matching firmware, auxiliary storage or disk inputs are reported
as missing inputs, never as a successful boot. The current builder does not
embed those Apple inputs. When an explicitly selected USB data partition is
mounted, the menu reads `/data/boot-profile.json` instead.

If the explicit profile contains `storage_session`, the menu selects
`boot-session --directory ...`; otherwise it selects the bounded read-only
`boot-probe`. The image includes `qemu-img` and its libraries for the separate
COW storage workflow. Any supplied session paths must already refer to an
explicitly configured storage location. A launch or probe exit is never counted
as a successful macOS boot.

`--data-size-mib N` adds a second GPT partition formatted as ext4. This supports
base disks and qcow2 overlays larger than FAT32's 4 GiB file limit. The builder
generates its PARTUUID and embeds `venfire.data_partuuid=<UUID>` in the GRUB
kernel command line. Without that selector the data code performs no device
discovery. With it, discovery begins at `/sys/bus/usb/devices`, accepts only
partition nodes whose real `/sys/devices` ancestry contains a USB subsystem,
and probes only those USB partitions with `blkid -p`. Exactly one matching
GPT PARTUUID is required. An internal NVMe/SATA partition with that UUID is not
probed or accepted. Duplicate UUIDs on attached USB devices are rejected.

The selected partition is first mounted as ext4 `ro,noload,nodev,nosuid` to
validate `VENFIRE_DATA.json` against the UUID and build profile. It is unmounted,
its USB identity is checked again, then mounted writable at `/data` with
`nodev,nosuid`. A missing or inconsistent marker fails before the writable
mount. This is scoped USB data access; root and normal diagnostic logs remain
in RAM. No scan of internal block devices or implicit partition mounting is
performed. The builder does not yet import Apple guest files into this data
partition; a future provisioning action must explicitly supply their paths.

For a self-authored large-file test, add `--data-size-mib 6144 --data-fixture`.
It creates a sparse base file of 5 GiB + 8192 bytes, with a sentinel beyond 5 GiB.
The live test creates a qcow2 overlay, writes and reads 4096 bytes at offset
5 GiB, checks the original zero block and sentinel, then fsyncs a USB evidence
log. On a subsequent boot it reads the previous overlay contents **before**
writing, so a fresh write cannot hide a persistence failure. This fixture
contains no Apple code. The large-file test checks the exact size and relevant
base samples; it does not substitute for whole-file provenance hashing of real
guest inputs.

Run the generated fixture image under OVMF twice with new evidence directories:

```sh
python3 usb/verify_uefi.py --image /path/to/fixture.img --output /tmp/uefi-first \
  --expect-data --expect-large-cow
python3 usb/verify_uefi.py --image /path/to/fixture.img --output /tmp/uefi-second \
  --expect-data --expect-large-cow --expect-cow-reopen
```

These flags enable writes to the supplied **regular image file** for the data
test; the default verification path attaches its image read-only. The verifier
rejects block devices and symlinks, uses a private OVMF variable file, disables
the PS/2 controller, and requires input through the attached USB keyboard.

`--autotest` selects a GRUB entry that runs startup checks and powers off.
For interactive verification, boot the ordinary image under OVMF with
`qemu-xhci`, `usb-storage` and `usb-kbd`. Use an explicit Intel AVX2 virtual CPU
such as `-cpu max,vendor=GenuineIntel`; the default max vendor can intentionally
fail central policy. Keep the image read-only and use a private OVMF variable
file. Capture serial markers and verify visible output and keyboard input.

This is an unsigned UEFI loader. Actual hardware acceptance still requires an
Intel Mac with 64-bit UEFI, suitable firmware policy, Intel+AVX2, working USB and
display output. The builder does not change firmware security settings. No
claim is made for 32-bit EFI Macs, a physical USB boot, or macOS usability until
those exact layers are tested.

Primary references: [Linux initramfs](https://www.kernel.org/doc/html/latest/filesystems/ramfs-rootfs-initramfs.html),
[initramfs archive format](https://cdn.kernel.org/doc/html/latest/driver-api/early-userspace/buffer-format.html),
[GNU GRUB removable EFI installation](https://www.gnu.org/software/grub/manual/grub/html_node/Installing-GRUB-using-grub_002dinstall.html),
and [QEMU USB emulation](https://www.qemu.org/docs/master/system/devices/usb.html).
USB ancestry follows the [Linux sysfs rules](https://www.kernel.org/doc/html/latest/admin-guide/sysfs-rules.html);
partition probing uses [blkid low-level PART_ENTRY_UUID](https://www.man7.org/linux/man-pages/man8/blkid.8.html).
Network setup uses the [BusyBox DHCP and interface applets](https://busybox.net/downloads/BusyBox.html)
and [QEMU network emulation](https://www.qemu.org/docs/master/system/devices/net.html).
