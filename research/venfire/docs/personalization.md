# Original firmware personalization

Layer: host userspace restore transport and request encoding. Apple's original
guest ROM remains responsible for IMG4 verification and execution. Obtaining a
ticket or reaching a DFU transfer state does not prove that the guest accepted
the signature or booted macOS.

`personalize-ibss` reads the live ROM's USB device and string descriptors,
requires production/secure DFU idle state, and selects exactly one full restore
BuildManifest identity by the actual guest CPID, BDID and security domain. It
checks the original iBSS against that manifest's digest. The private ECID and
fresh nonce values come from this running VM; no physical Mac identity,
provisioned AUX storage or another VM's ticket is imported.

The pinned `tools/tss_request.c` helper uses libtatsu only to encode a request.
The Python client sends that request to Apple's official HTTPS TSS endpoint
with certificate and hostname verification, no redirect and no HTTP fallback.
Apple's public PKI root is pinned and loaded only in this client's SSL context;
see [certificate provenance](../venfire/certs/README.md). The upstream libtatsu
network sender is deliberately not called because it disables certificate
verification and has fallback endpoints.

The client re-reads the guest nonce after the response and rejects any change.
It places the unchanged IM4P and the server-issued IM4M in a standard IMG4
container. This is ordinary firmware personalization: no instructions, trust
checks, signatures or tickets are synthesized or patched. Original input and
helper hashes are checked before and after the operation. Private requests,
nonces, tickets and firmware stay in the selected private work directory and
are not bundled in release artifacts.

Build the offline helper on Linux with `tools/build_restore_tools.py`. Its
build receipt records the pinned libplist/libtatsu source revisions and helper
hash. The USB builder's optional restore-helper support includes the required
shared libraries; a functioning network and trusted clock are needed for TSS.

An explicit developer host bypass is accepted only in a private developer tree
created by `tools/create_developer_tree.py`. Intel x86_64/AVX2 remains required.

```sh
python3 -m venfire personalize-ibss \
  --socket /tmp/venfire-recovery.sock \
  --manifest /private/BuildManifest.plist \
  --ibss /private/iBSS.vma2.RELEASE.im4p \
  --helper /private/prefix/bin/venfire-tss-request \
  --output /private/fresh-personalization-directory \
  --developer-host-bypass
```

Use the resulting hash and the same still-running VM for `dfu-upload`. A VM
restart can invalidate the nonce binding. The host transport sends 2048-byte
blocks as one type-1 setup/data packet each, includes the standard DFU CRC
suffix, and requires the actual six-byte guest status responses. Empty replies
are errors. `--reset` means a virtual USB bus reset, never a host reboot.

The verified chain now reaches original Monterey XNU EL1 execution, followed by
an IOKit Sleep/Wake watchdog panic. Original macOS 27 iBSS reaches its recovery
prompt and original iBEC begins execution. These are separate milestones from
restore userspace, installation, desktop operation and physical USB boot.
See `apple-boot.md` and the per-stage evidence for exact observations.

`personalize-firmware --component iBEC --include-restore-policy` obtains the
standard restore LocalPolicy with `Ap,NextStageIM4MHash` equal to SHA-384 of the
entire iBEC IM4M ticket. The subsequent restore must keep that exact ticket:
another successful TSS response can differ even with the same live nonce.
`tools/restore_stage.py --boot --chain-personalization <iBEC directory>` uses
`reuse_restore_ticket`, verifies the saved original inputs and identity against
the official manifest, rechecks live ECID/NONC/SNON, validates LocalPolicy's
binding and copies the same ticket. It does not send a new network request.
The guest's signature and LocalPolicy checks remain authoritative.

BuildManifest reads are bounded to 32 MiB. Restore component digests use 1 MiB
streaming reads. Helper stdout and stderr have independent bounds and a deadline.
If inputs change during the final check, generated ticket/firmware outputs are
removed and success flags are revoked. Error stage and input integrity are saved
even when the operation fails or is interrupted.

Protocol/reference sources:

- [libirecovery](https://github.com/libimobiledevice/libirecovery), revision
  `95dec3aa25b1e30654ca107eb971971f6a216520`: USB nonce descriptors, DFU suffix,
  CRC and status handling.
- [libtatsu](https://github.com/libimobiledevice/libtatsu), revision
  `60a39f36d719344360ec2e87563ed43f61f0530f`: public request encoding APIs.
- [idevicerestore IMG4 wrapper](https://github.com/libimobiledevice/idevicerestore/blob/540c352c4c44896f7415abef87a166e8bbaea9b0/src/img4.c)
  and [DFU stage progression](https://github.com/libimobiledevice/idevicerestore/blob/540c352c4c44896f7415abef87a166e8bbaea9b0/src/dfu.c):
  unmodified component wrapping and fresh nonce checks between stages.
- [Apple PKI directory](https://www.apple.com/certificateauthority/): public
  root certificate source, independently retrieved over verified HTTPS.
