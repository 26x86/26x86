// Authored architectural CPU probe. No vendor firmware or private registers.
// x19 is the active check, x20 the passed-check bitmap, x0 the final marker.
.arch armv8.3-a
.text
.global _start
_start:
    mov x0, #0xa11
    mov x19, #1
    mov x20, #0
    mrs x21, CurrentEL
    cmp x21, #4
    b.ne failed
    msr daifset, #15
    orr x20, x20, #1

    mov x19, #2
    mrs x22, ID_AA64ISAR1_EL1
    ubfx x3, x22, #4, #4       // APA: QARMA5 address authentication.
    cbz x3, failed
    orr x20, x20, #2

    mov x19, #3
    mrs x23, ID_AA64MMFR0_EL1
    ubfx x3, x23, #20, #4      // TGran16: 1=16K, 2=16K with LPA2.
    cmp x3, #1
    b.lo failed
    cmp x3, #2
    b.hi failed
    orr x20, x20, #4

    mov x19, #4
    mrs x24, CNTFRQ_EL0
    mov x3, #0x3600
    movk x3, #0x16e, lsl #16  // 24,000,000 Hz, matching recovery launch.
    cmp x24, x3
    b.ne failed
    mrs x25, CNTPCT_EL0       // Must not trap to uninitialised EL2 vectors.
    mov x3, #0xffff
1:  subs x3, x3, #1
    b.ne 1b
    mrs x26, CNTPCT_EL0
    cmp x26, x25
    b.ls failed
    orr x20, x20, #8

    mov x19, #5
    mov x10, #0x1357
    movk x10, #0x2468, lsl #16
    movk x10, #0x369c, lsl #32
    movk x10, #0x48ad, lsl #48
    mvn x11, x10
    msr APIAKeyLo_EL1, x10
    msr APIAKeyHi_EL1, x11
    isb
    mrs x12, APIAKeyLo_EL1
    mrs x13, APIAKeyHi_EL1
    cmp x12, x10
    b.ne failed
    cmp x13, x11
    b.ne failed
    orr x20, x20, #16

    mov x19, #6
    mrs x27, SCTLR_EL1
    tbnz x27, #0, failed      // The controlled probe requires MMU-off entry.
    // Define 48-bit pointer ranges with 16K granules; keep MMU disabled.
    mov x3, #0x8010           // T0SZ=16, TG0=2.
    movk x3, #0x4010, lsl #16 // T1SZ=16, TG1=1.
    movk x3, #5, lsl #32     // IPS=48 bits.
    msr TCR_EL1, x3
    orr x3, x27, #0x80000000 // SCTLR.EnIA enables actual signing.
    msr SCTLR_EL1, x3
    isb
    adr x4, authenticated
    mov x5, x4
    mov x6, #0x9876
    pacia x5, x6
    cmp x5, x4               // A disabled/no-op PAC must not pass.
    b.eq failed
    mov x28, x5
    autia x5, x6
    cmp x5, x4
    b.ne failed
    orr x20, x20, #32

    mov x19, #7
    mov x5, x28
    braa x5, x6
    b failed
authenticated:
    orr x20, x20, #64
    mov x19, #0
    mov x0, #0x64e
    b parked
failed:
    mov x0, #0xbad
parked:
    // WFI can trap to EL2 on a broken reset profile; an inert branch cannot.
    b parked
