# VMApple BARRIER: host device-model flush patch

This change is at the **QEMU user-space device-model and block-backend layer**.
It modifies no macOS image, kernel, driver, signature, or guest instruction.
`patches/0002-vmapple-block-barrier.patch` replaces immediate success for Apple
opcode `0x10000` with QEMU's existing asynchronous virtio-blk flush handler.
This is a concrete durability improvement over the existing no-op. It is **not
evidence that Apple's complete barrier contract has been implemented**.

The base is QEMU commit `ff1d2d19d7e24893e2012d879f8e73077e17b9bd`.
The patch touches three files: `hw/vmapple/virtio-blk.c`,
`hw/block/virtio-blk.c`, and `include/hw/virtio/virtio-blk.h`. It does not overlap
the files in patch 0001. Each modified file retains its upstream license.

The pinned VMApple implementation identifies the extra opcode as BARRIER but
immediately completes it with `VIRTIO_BLK_S_OK`. That source does not specify
the signed Apple driver's ordering, queue scope, data format, or persistence
requirements. In particular, Apple's `0x10000` is a different opcode from the
legacy virtio barrier bit `0x80000000`. Treating the two contracts as identical
would be an inference, not a verified ABI fact.
[Pinned VMApple implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/vmapple/virtio-blk.c).

The patch exposes `virtio_blk_handle_flush()` for device subclasses and calls
it from the Apple handler. The helper submits pending writes in the current
`MultiReqBuffer`, starts flush accounting, and submits `blk_aio_flush()`.
Its callback owns request completion and lifetime. With `werror=report`, a
flush failure completes with `VIRTIO_BLK_S_IOERR`; `werror=stop` retains the
request for recovery. `werror=ignore` can acknowledge failed flushes and is
unsuitable for this use. Ordinary virtio-blk flush behavior is unchanged.
The virtqueue loop still processes subsequent requests asynchronously; this
patch introduces no global queue drain or fence.
[Pinned virtio-blk helper and callbacks](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/block/virtio-blk.c).

Flush and ordering must be tested separately. The VIRTIO 1.3 persistence
condition includes a write completing, a flush being submitted afterward,
and that flush completing. Its legacy barrier describes ordering of preceding
and following requests and does not itself flush host caches. Consequently,
reusing FLUSH does not establish the stronger proposition that every request
submitted before an Apple barrier has completed, or that later requests cannot
start before the barrier completes. Multiple queues make that distinction
especially important; using one queue alone does not prove a full fence.
[VIRTIO 1.3 sections 5.2.6.2 and 5.2.6.3](https://docs.oasis-open.org/virtio/virtio/v1.3/virtio-v1.3.html).

For persistent session storage, the required configuration is a writable local
qcow2 overlay, a read-only raw backing image, `cache.no-flush=false` throughout
the writable graph, and a reporting or stopping write-error policy. Do not use
`cache=unsafe`. QEMU's block flush walks writable children; `BDRV_O_NO_FLUSH`
can skip forcing data to disk, and a backend without a flush implementation
can still return success. Therefore a successful callback alone cannot prove
physical persistence on arbitrary storage. A RAM overlay lasts only as long as
its host memory. Sharing one qcow2 node between the read-only BDIF view and the
runtime virtio view supplies coherent visibility, not a second persistence
guarantee.
[Pinned block flush implementation](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/block/io.c).

The following validation separates what this patch implements from what still
requires evidence. Use disposable synthetic base files and overlays; no Apple
guest or physical disk is needed for the device tests.

1. Apply the two patches to the exact base, build the aarch64 system emulator,
   and record the source diff, both patch hashes, and executable hash. A clean
   build proves the public helper is declared and linked. It does not exercise
   the opcode.
2. Extend the existing virtio-blk qtest request machinery to address the Apple
   PCI device and submit a header with type `0x10000`, sector zero, and a status
   descriptor. Use the same synthetic fixture for the standard FLUSH control.
   An HMP `qemu-io ... flush` command directly exercises the backend and cannot
   substitute for this test of Apple-opcode dispatch.
3. Complete a known-pattern write, then submit the Apple request. Delay the
   backend flush through a test filter and verify that the request's used-ring
   completion is absent until the flush is released. Inject a flush error
   after a completed dirty write: with `werror=report`, require IOERR rather
   than OK, exactly one completion, and no leaked or double-freed request.
   Repeat success, standard FLUSH, and unrelated unsupported-opcode cases.
4. Submit multiple writes followed by the Apple opcode in one virtqueue kick.
   Trace submission, backend completion, and used-ring completion. Verify that
   writes buffered by request merging reach the backend before flush
   submission. Separately delay an earlier write and submit a later write
   around the barrier, then repeat across two queues. These cases determine
   whether a stronger fence is required; the minimal patch does not promise
   that later requests wait. Add a queue-ordering design only after the actual
   Apple contract or an authorized driver trace establishes its scope.
5. After a completed write followed by a successful Apple request, terminate
   the emulator without its normal close path, reopen the overlay, and verify
   the pattern plus qcow2 consistency. Check that both original base hashes
   remain identical. This verifies process-crash recovery. A separate storage
   fault or controlled host-power-loss test is needed to establish persistence
   beyond host caches and the device's own reported flush behavior.

The existing upstream qtest implementation provides request construction and
completion checks that can be adapted for the synthetic fixture.
[Pinned virtio-blk qtests](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/tests/qtest/virtio-blk-test.c).

At patch creation, `git apply --check`, application, and reverse-application
checks passed against separately downloaded files from the exact commit.
A read-only `git apply --check` also passed against the existing local checkout
with patch 0001. Patch SHA-256:
`58e8a2a42656647f7e3f8393e1b032fc260b99760ce37576c00b7af0938473cc`.
Those patch checks alone do not establish runtime behavior.

`tools/verify_barrier.py` now exercises the Apple opcode through real QEMU PCI
MMIO, feature negotiation, split-ring descriptors, queue notification, and
used-ring completion. It uses the `virt,highmem=off` machine with the qtest
accelerator and an Apple virtio-blk PCI device. No CPU executes guest code. All
disk paths are created by the verifier in a disposable directory; it accepts
no guest image or firmware argument. The layout follows the pinned
[virtio PCI header](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/include/standard-headers/linux/virtio_pci.h)
and the [virt machine memory map](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/hw/arm/virt.c).

The rebuilt executable with SHA-256
`0798b6d00154a5cc3497bdef4519c9e346cdc4f10138ccb2c4421baf71612548`
passed all five cases: Apple flush success, Apple flush delayed by 200 ms,
Apple delayed EIO, and delayed standard-FLUSH success/EIO controls. Apple EIO
returned status 1 (IOERR), and the delayed requests did not complete before
the configured delay. Every case also completed a write, verified its readback,
rejected an unrelated opcode with status 2 (UNSUPP), and checked the used-ring
completion count. The QEMU executable's manifest was checked before each case
and after the run. The complete result is in
[storage-barrier.json](../evidence/storage-barrier.json).

Run a fresh result on Linux or WSL with:

```sh
python3 tools/verify_barrier.py --qemu /absolute/path/qemu-system-aarch64 \
    --output /new/path/storage-barrier.json
```

The error/delay filter uses QEMU's documented `blkdebug` `flush_to_disk` event
and flush-only injection. At this pinned revision, its delay uses the host
real-time clock, so the test measures elapsed wall time rather than assuming
that advancing qtest virtual time advances the delay.
[Pinned blkdebug filter](https://github.com/qemu/qemu/blob/ff1d2d19d7e24893e2012d879f8e73077e17b9bd/block/blkdebug.c).
The passing cases establish opcode dispatch and asynchronous flush/error
completion. They do not establish full or multiqueue ordering, allocation leak
freedom under sanitizers, host power-loss persistence, signed Apple-driver
interoperability, or macOS boot.
