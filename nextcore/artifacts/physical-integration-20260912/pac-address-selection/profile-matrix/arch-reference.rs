//! Explicit AArch64 guest architectural state and a bounded reference core.
//!
//! EFI owns the outer lifecycle and the C JIT owns host code emission. This
//! module owns only guest architectural state. The reference core is used for
//! the privileged/MMU contract tests and for feature-requested runs; the
//! existing base JIT remains the fast path for the original diagnostic guest.
//! A step is committed only after decode, translation, and permission checks.

#![allow(dead_code)]

use super::mmu::{Access, Fault as MmuFault, VfMmu};
use super::pauth::{self, PauthContext, PauthState};

/// Guest physical memory boundary used by the reference execution core.
///
/// The bus is deliberately smaller than a general address-space framework: it
/// only supplies bounded reads/writes and a host-side code-load operation.  EFI
/// pointers never cross this trait.  A machine can add MMIO without teaching
/// the architectural decoder about a particular device.
pub(crate) trait GuestBus {
    /// Copy an immutable test image into guest RAM before the first fetch.
    /// This is a loader operation, not an emulated guest store, and therefore
    /// does not use guest translation or MMIO side effects.
    fn load_code(&mut self, code: &[u8]) -> bool;

    fn read(
        &mut self,
        address: u64,
        size: usize,
        access: Access,
    ) -> Result<u64, ExceptionKind>;

    fn write(
        &mut self,
        address: u64,
        size: usize,
        value: u64,
        access: Access,
    ) -> Result<(), ExceptionKind>;

    /// Each scalar read/write validates its entire element before committing
    /// side effects. The caller supplies one complete 1/2/4/8-byte transfer.
    /// Pair operations require RAM preflight before either transfer. A bus
    /// with MMIO must explicitly opt in; scalar accesses are not a preflight.
    fn pair_ram(&mut self) -> Option<(&mut [u8], u64)> { None }

    /// Device graphs use this hook to observe an architecturally committed
    /// instruction.  The default RAM bus has no device clock to update.
    fn after_instruction(&mut self, _state: &mut GuestCpuState) {}
}

struct RamBus<'a> {
    ram: &'a mut [u8],
    base: u64,
}

impl<'a> RamBus<'a> {
    fn new(ram: &'a mut [u8]) -> Self {
        Self { ram, base: 0 }
    }
}

impl GuestBus for RamBus<'_> {
    fn pair_ram(&mut self) -> Option<(&mut [u8], u64)> { Some((self.ram, self.base)) }
    fn load_code(&mut self, code: &[u8]) -> bool {
        if code.len() > self.ram.len() {
            return false;
        }
        self.ram[..code.len()].copy_from_slice(code);
        true
    }

    fn read(
        &mut self,
        address: u64,
        size: usize,
        _access: Access,
    ) -> Result<u64, ExceptionKind> {
        let offset = address.checked_sub(self.base).ok_or(ExceptionKind::DataAbort)?;
        read_width(self.ram, usize::try_from(offset).unwrap_or(usize::MAX), size)
            .ok_or(ExceptionKind::DataAbort)
    }

    fn write(
        &mut self,
        address: u64,
        size: usize,
        value: u64,
        _access: Access,
    ) -> Result<(), ExceptionKind> {
        let offset = address.checked_sub(self.base).ok_or(ExceptionKind::DataAbort)?;
        let index = usize::try_from(offset).map_err(|_| ExceptionKind::DataAbort)?;
        write_width(self.ram, index, size, value)
            .then_some(())
            .ok_or(ExceptionKind::DataAbort)
    }
}

pub(crate) const PSTATE_N: u32 = 1 << 31;
pub(crate) const PSTATE_Z: u32 = 1 << 30;
pub(crate) const PSTATE_C: u32 = 1 << 29;
pub(crate) const PSTATE_V: u32 = 1 << 28;
pub(crate) const PSTATE_D: u32 = 1 << 9;
pub(crate) const PSTATE_A: u32 = 1 << 8;
pub(crate) const PSTATE_I: u32 = 1 << 7;
pub(crate) const PSTATE_F: u32 = 1 << 6;

const SCTLR_M: u64 = 1 << 0;
const SCTLR_A: u64 = 1 << 1;
const CNTP_CTL_ENABLE: u64 = 1 << 0;
const CNTP_CTL_IMASK: u64 = 1 << 1;
const CNTP_CTL_ISTATUS: u64 = 1 << 2;
const M1_COUNTER_FREQUENCY: u64 = 24_000_000;
const PSTATE_MODE_MASK: u32 = 0x0f;

fn mode_for_el(level: ExceptionLevel) -> u32 {
    match level {
        ExceptionLevel::El0 => 0,
        ExceptionLevel::El1 => 5,
        // AArch64 PSTATE.M[3:0]: EL1t/EL1h=4/5,
        // EL2t/EL2h=8/9, EL3t/EL3h=12/13.  The reference reset state uses
        // the h (current-EL stack) form at each privileged level.
        ExceptionLevel::El2 => 9,
        ExceptionLevel::El3 => 13,
    }
}

fn level_for_mode(mode: u32) -> Option<ExceptionLevel> {
    match mode & PSTATE_MODE_MASK {
        0 => Some(ExceptionLevel::El0),
        4 | 5 => Some(ExceptionLevel::El1),
        8 | 9 => Some(ExceptionLevel::El2),
        12 | 13 => Some(ExceptionLevel::El3),
        _ => None,
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub(crate) enum ExceptionKind {
    UndefinedInstruction = 1,
    PrivilegedInstruction = 2,
    InstructionAbort = 3,
    DataAbort = 4,
    TranslationFault = 5,
    PermissionFault = 6,
    AlignmentFault = 7,
    SystemRegisterTrap = 8,
    TimerInterrupt = 9,
    ExternalInterrupt = 10,
    GuestHalt = 11,
    SupervisorCall = 12,
    FiqInterrupt = 13,
    SpAlignmentFault = 14,
}

const ESR_EC_UNKNOWN: u64 = 0x00;
const ESR_EC_SVC64: u64 = 0x15;
const ESR_EC_SYSREG: u64 = 0x18;
const ESR_EC_IABT_LOWER: u64 = 0x20;
const ESR_EC_IABT_SAME: u64 = 0x21;
const ESR_EC_DABT_LOWER: u64 = 0x24;
const ESR_EC_DABT_SAME: u64 = 0x25;
const ESR_FSC_TRANSLATION_L3: u64 = 0x07;
const ESR_FSC_ACCESS_FLAG_L3: u64 = 0x09;
const ESR_FSC_PERMISSION_L3: u64 = 0x0d;
const ESR_FSC_ALIGNMENT: u64 = 0x21;
const ESR_ISS_WNR: u64 = 1 << 6;
const INTERNAL_ACCESS_WNR: u64 = 1 << 22;

fn encoded_ec(syndrome: u64) -> u64 {
    syndrome >> 26
}

fn expected_ec(kind: ExceptionKind, source_el: ExceptionLevel) -> Option<u64> {
    match kind {
        ExceptionKind::SpAlignmentFault => Some(0x26),
        ExceptionKind::SupervisorCall => Some(ESR_EC_SVC64),
        ExceptionKind::SystemRegisterTrap => Some(ESR_EC_SYSREG),
        ExceptionKind::InstructionAbort => Some(if source_el == ExceptionLevel::El0 {
            ESR_EC_IABT_LOWER
        } else {
            ESR_EC_IABT_SAME
        }),
        ExceptionKind::DataAbort
        | ExceptionKind::TranslationFault
        | ExceptionKind::PermissionFault
        | ExceptionKind::AlignmentFault => Some(if source_el == ExceptionLevel::El0 {
            ESR_EC_DABT_LOWER
        } else {
            ESR_EC_DABT_SAME
        }),
        _ => None,
    }
}

/// Convert the internal exception payload into the ESR_ELx value visible to a
/// guest handler.  Decoder call sites pass the raw instruction as a compact
/// ISS source; direct state-model callers may pass an already encoded ESR.
/// The latter is retained only when its EC agrees with the exception class.
fn exception_syndrome(
    kind: ExceptionKind,
    source_el: ExceptionLevel,
    supplied: u64,
) -> u64 {
    if let Some(ec) = expected_ec(kind, source_el) {
        if encoded_ec(supplied) == ec {
            return supplied;
        }
    }
    match kind {
        ExceptionKind::SpAlignmentFault => (0x26 << 26) | (1 << 25),
        ExceptionKind::SupervisorCall => {
            (ESR_EC_SVC64 << 26) | (supplied & 0xffff)
        }
        ExceptionKind::SystemRegisterTrap => {
            (ESR_EC_SYSREG << 26) | (supplied & 0x01ff_ffff)
        }
        ExceptionKind::InstructionAbort => {
            let ec = expected_ec(kind, source_el).unwrap_or(ESR_EC_IABT_SAME);
            (ec << 26) | ESR_FSC_TRANSLATION_L3
        }
        ExceptionKind::DataAbort
        | ExceptionKind::TranslationFault
        | ExceptionKind::PermissionFault
        | ExceptionKind::AlignmentFault => {
            let ec = expected_ec(kind, source_el).unwrap_or(ESR_EC_DABT_SAME);
            let fsc = match kind {
                ExceptionKind::PermissionFault => ESR_FSC_PERMISSION_L3,
                ExceptionKind::AlignmentFault => ESR_FSC_ALIGNMENT,
                // Access-flag faults are currently normalized by the MMU
                // adapter to TranslationFault.  Keep the distinct FSC here
                // for callers that provide that value as the low ISS.
                ExceptionKind::TranslationFault if supplied & 0x3f == ESR_FSC_ACCESS_FLAG_L3 => {
                    ESR_FSC_ACCESS_FLAG_L3
                }
                _ => ESR_FSC_TRANSLATION_L3,
            };
            let wnr = if supplied & (1 << 22) != 0 {
                ESR_ISS_WNR
            } else {
                0
            };
            (ec << 26) | wnr | fsc
        }
        // Undefined and privilege failures have no architecturally useful
        // ISS in this boundary.  Their internal ExceptionKind remains the
        // precise classification returned to the host.
        ExceptionKind::UndefinedInstruction | ExceptionKind::PrivilegedInstruction => {
            // EC0 requires IL=1 and ISS=0; raw opcode bits never become ISS.
            (ESR_EC_UNKNOWN << 26) | (1 << 25)
        }
        ExceptionKind::TimerInterrupt
        | ExceptionKind::ExternalInterrupt
        | ExceptionKind::FiqInterrupt
        | ExceptionKind::GuestHalt => 0,
    }
}

fn access_syndrome(access: Access) -> u64 {
    match access {
        // Decoder paths use bit 22 as a private write/read hint.  The public
        // ESR WnR bit is bit 6 and is emitted only by exception_syndrome(),
        // after the exception class and source EL are known.
        Access::Write => INTERNAL_ACCESS_WNR,
        Access::Read | Access::Execute => 0,
    }
}

fn logical_immediate(word: u32) -> Option<u64> {
    let width=if word>>31!=0 {64} else {32};
    let n=(word>>22)&1;let imms=(word>>10)&63;let immr=(word>>16)&63;
    if width==32 && n!=0 { return None; }
    let tag=(n<<6)|(!imms&63);
    if tag<2 { return None; }
    let len=31-tag.leading_zeros();let size=1u32<<len;let levels=size-1;
    let s=imms&levels;let r=immr&levels;
    if size>width || s==levels { return None; }
    let mut element=(1u64<<(s+1))-1;
    if r!=0 { element=(element>>r)|(element<<(size-r)); }
    if size<64 { element&=(1u64<<size)-1; }
    let mut mask=0;let mut at=0;
    while at<width {mask|=element<<at;at+=size;}
    Some(mask)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct GuestException {
    pub(crate) kind: ExceptionKind,
    /// The raw A64 word that caused a synchronous exception.  Asynchronous
    /// exceptions and fetch faults have no decoded word and use zero.  Keep
    /// this separate from `syndrome`: ESR_ELx is the guest-visible encoding,
    /// while the ABI result's `fault_instruction` field must remain the
    /// actual faulting instruction.
    pub(crate) instruction: u32,
    pub(crate) syndrome: u64,
    pub(crate) far: u64,
    pub(crate) pc: u64,
}

pub(crate) use super::exception_level::ExceptionLevel;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SysRegFault {
    Undefined,
    Privilege,
    Unknown,
    ReadOnly,
    InvalidValue,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub(crate) enum SystemRegister {
    SctlrEl1 = 1,
    Ttbr0El1 = 2,
    Ttbr1El1 = 3,
    TcrEl1 = 4,
    MairEl1 = 5,
    VbarEl1 = 6,
    EsrEl1 = 7,
    FarEl1 = 8,
    ElrEl1 = 9,
    SpsrEl1 = 10,
    CntfrqEl0 = 11,
    CntpctEl0 = 12,
    CntpCtlEl0 = 13,
    CntpCvalEl0 = 14,
    CurrentEl = 15,
    IdAa64Mmfr0El1 = 16,
    IdAa64Isar1El1 = 17,
    CntvctEl0 = 18,
    CntvCtlEl0 = 19,
    CntvCvalEl0 = 20,
    CntpTvalEl0 = 21,
    HcrEl2 = 22,
    CnthctlEl2 = 23,
    VbarEl2 = 24,
    EsrEl2 = 25,
    FarEl2 = 26,
    ElrEl2 = 27,
    SpsrEl2 = 28,
    ScrEl3 = 29,
    VbarEl3 = 30,
    EsrEl3 = 31,
    FarEl3 = 32,
    ElrEl3 = 33,
    SpsrEl3 = 34,
    TpidrEl0 = 35,
    TpidrroEl0 = 36,
    TpidrEl1 = 37,
    PlatformOverride = 38,
    IdAa64Zfr0El1 = 39,
    IdAa64Isar0El1 = 40,
}

impl SystemRegister {
    /// Match the architectural encodings after the Rt field is cleared. The
    /// two opcodes for a register (MRS and MSR) are listed together because
    /// the access direction is decided by the instruction decoder.
    fn from_instruction(word: u32) -> Option<Self> {
        match word & !31 {
            0xd538_0480 => Some(Self::IdAa64Zfr0El1),
            0xd538_0600 => Some(Self::IdAa64Isar0El1),
            0xd53d_f500 | 0xd51d_f500 => Some(Self::PlatformOverride),
            0xd53b_d040 | 0xd51b_d040 => Some(Self::TpidrEl0),
            0xd53b_d060 | 0xd51b_d060 => Some(Self::TpidrroEl0),
            0xd538_d080 | 0xd518_d080 => Some(Self::TpidrEl1),
            0xd538_1000 | 0xd518_1000 => Some(Self::SctlrEl1),
            0xd538_2000 | 0xd518_2000 => Some(Self::Ttbr0El1),
            0xd538_2020 | 0xd518_2020 => Some(Self::Ttbr1El1),
            0xd538_2040 | 0xd518_2040 => Some(Self::TcrEl1),
            0xd538_a200 | 0xd518_a200 => Some(Self::MairEl1),
            0xd538_c000 | 0xd518_c000 => Some(Self::VbarEl1),
            0xd538_5200 | 0xd518_5200 => Some(Self::EsrEl1),
            0xd538_6000 | 0xd518_6000 => Some(Self::FarEl1),
            0xd538_4020 | 0xd518_4020 => Some(Self::ElrEl1),
            0xd538_4000 | 0xd518_4000 => Some(Self::SpsrEl1),
            0xd53b_e000 | 0xd51b_e000 => Some(Self::CntfrqEl0),
            0xd53b_e020 | 0xd51b_e020 => Some(Self::CntpctEl0),
            0xd53b_e220 | 0xd51b_e220 => Some(Self::CntpCtlEl0),
            0xd53b_e240 | 0xd51b_e240 => Some(Self::CntpCvalEl0),
            0xd538_4240 => Some(Self::CurrentEl),
            0xd538_0700 | 0xd518_0700 => Some(Self::IdAa64Mmfr0El1),
            0xd538_0620 | 0xd518_0620 => Some(Self::IdAa64Isar1El1),
            0xd53b_e040 | 0xd51b_e040 => Some(Self::CntvctEl0),
            0xd53b_e320 | 0xd51b_e320 => Some(Self::CntvCtlEl0),
            0xd53b_e340 | 0xd51b_e340 => Some(Self::CntvCvalEl0),
            0xd53b_e200 | 0xd51b_e200 => Some(Self::CntpTvalEl0),
            0xd53c_1100 | 0xd51c_1100 => Some(Self::HcrEl2),
            0xd53c_e100 | 0xd51c_e100 => Some(Self::CnthctlEl2),
            0xd53c_c000 | 0xd51c_c000 => Some(Self::VbarEl2),
            0xd53c_5200 | 0xd51c_5200 => Some(Self::EsrEl2),
            0xd53c_6000 | 0xd51c_6000 => Some(Self::FarEl2),
            0xd53c_4020 | 0xd51c_4020 => Some(Self::ElrEl2),
            0xd53c_4000 | 0xd51c_4000 => Some(Self::SpsrEl2),
            0xd53e_1100 | 0xd51e_1100 => Some(Self::ScrEl3),
            0xd53e_c000 | 0xd51e_c000 => Some(Self::VbarEl3),
            0xd53e_5200 | 0xd51e_5200 => Some(Self::EsrEl3),
            0xd53e_6000 | 0xd51e_6000 => Some(Self::FarEl3),
            0xd53e_4020 | 0xd51e_4020 => Some(Self::ElrEl3),
            0xd53e_4000 | 0xd51e_4000 => Some(Self::SpsrEl3),
            _ => None,
        }
    }

    fn minimum_el(self) -> ExceptionLevel {
        match self {
            Self::TpidrEl0 | Self::TpidrroEl0 => ExceptionLevel::El0,
            Self::CntfrqEl0
            | Self::CntpctEl0
            | Self::CntpCtlEl0
            | Self::CntpCvalEl0
            | Self::CurrentEl
            | Self::CntvctEl0
            | Self::CntvCtlEl0
            | Self::CntvCvalEl0
            | Self::CntpTvalEl0 => ExceptionLevel::El0,
            Self::IdAa64Mmfr0El1 | Self::IdAa64Isar1El1 => ExceptionLevel::El1,
            Self::HcrEl2
            | Self::CnthctlEl2
            | Self::VbarEl2
            | Self::EsrEl2
            | Self::FarEl2
            | Self::ElrEl2
            | Self::SpsrEl2 => ExceptionLevel::El2,
            Self::ScrEl3
            | Self::VbarEl3
            | Self::EsrEl3
            | Self::FarEl3
            | Self::ElrEl3
            | Self::SpsrEl3 => ExceptionLevel::El3,
            _ => ExceptionLevel::El1,
        }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct SystemRegisters {
    pub(crate) tpidr_el0: u64,
    pub(crate) tpidrro_el0: u64,
    pub(crate) tpidr_el1: u64,
    pub(crate) sctlr_el1: u64,
    pub(crate) ttbr0_el1: u64,
    pub(crate) ttbr1_el1: u64,
    pub(crate) tcr_el1: u64,
    pub(crate) mair_el1: u64,
    pub(crate) vbar_el1: u64,
    pub(crate) esr_el1: u64,
    pub(crate) far_el1: u64,
    pub(crate) elr_el1: u64,
    pub(crate) spsr_el1: u64,
    pub(crate) cntfrq_el0: u64,
    pub(crate) cntpct_el0: u64,
    pub(crate) cntp_ctl_el0: u64,
    pub(crate) cntp_cval_el0: u64,
    pub(crate) id_aa64mmfr0_el1: u64,
    pub(crate) id_aa64isar1_el1: u64,
    pub(crate) cntvct_el0: u64,
    pub(crate) cntv_ctl_el0: u64,
    pub(crate) cntv_cval_el0: u64,
    pub(crate) cntp_tval_el0: u64,
    pub(crate) hcr_el2: u64,
    pub(crate) cnthctl_el2: u64,
    pub(crate) vbar_el2: u64,
    pub(crate) esr_el2: u64,
    pub(crate) far_el2: u64,
    pub(crate) elr_el2: u64,
    pub(crate) spsr_el2: u64,
    pub(crate) scr_el3: u64,
    pub(crate) vbar_el3: u64,
    pub(crate) esr_el3: u64,
    pub(crate) far_el3: u64,
    pub(crate) elr_el3: u64,
    pub(crate) spsr_el3: u64,
}

impl SystemRegisters {
    pub(crate) const fn reset() -> Self {
        Self {
            // Architectural reset is UNKNOWN. Choose deterministic zero, as
            // in the C bank; these software values are not memory addresses
            // interpreted by the PE. FGT/AArch32 aliases are not implemented.
            tpidr_el0: 0,
            tpidrro_el0: 0,
            tpidr_el1: 0,
            sctlr_el1: 0,
            ttbr0_el1: 0,
            ttbr1_el1: 0,
            tcr_el1: 16,
            mair_el1: 0,
            vbar_el1: 0,
            esr_el1: 0,
            far_el1: 0,
            elr_el1: 0,
            spsr_el1: 0,
            cntfrq_el0: M1_COUNTER_FREQUENCY,
            cntpct_el0: 0,
            cntp_ctl_el0: 0,
            cntp_cval_el0: 0,
            // Bounded 4K/16K translation and baseline QARMA5 authentication.
            // Enhanced PAuth, FPAC and generic authentication remain absent.
            id_aa64mmfr0_el1: 0x0010_1122,
            id_aa64isar1_el1: 0x10,
            cntvct_el0: 0,
            cntv_ctl_el0: 0,
            cntv_cval_el0: 0,
            cntp_tval_el0: 0,
            hcr_el2: 0,
            cnthctl_el2: 0,
            vbar_el2: 0,
            esr_el2: 0,
            far_el2: 0,
            elr_el2: 0,
            spsr_el2: 0,
            scr_el3: 0,
            vbar_el3: 0,
            esr_el3: 0,
            far_el3: 0,
            elr_el3: 0,
            spsr_el3: 0,
        }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct GenericTimer {
    pub(crate) frequency: u64,
    pub(crate) counter: u64,
    pub(crate) ctl: u64,
    pub(crate) cval: u64,
}

impl GenericTimer {
    pub(crate) const fn reset() -> Self {
        Self {
            frequency: M1_COUNTER_FREQUENCY,
            counter: 0,
            ctl: 0,
            cval: 0,
        }
    }

    pub(crate) fn pending(&self) -> bool {
        self.ctl & CNTP_CTL_ENABLE != 0
            && self.ctl & CNTP_CTL_IMASK == 0
            && self.counter >= self.cval
    }

    pub(crate) fn advance(&mut self, ticks: u64) {
        self.counter = self.counter.saturating_add(ticks);
        if self.pending() {
            self.ctl |= CNTP_CTL_ISTATUS;
        } else {
            self.ctl &= !CNTP_CTL_ISTATUS;
        }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct SmpState {
    pub(crate) cpu_count: u32,
    pub(crate) online_mask: u64,
    pub(crate) external_pending: u64,
}

impl SmpState {
    pub(crate) const fn reset() -> Self {
        Self {
            cpu_count: 1,
            online_mask: 1,
            external_pending: 0,
        }
    }

    pub(crate) fn set_cpu_count(&mut self, count: u32) -> bool {
        if count == 0 || count > 64 {
            return false;
        }
        self.cpu_count = count;
        self.online_mask &= if count == 64 {
            u64::MAX
        } else {
            (1u64 << count) - 1
        };
        if self.online_mask == 0 {
            self.online_mask = 1;
        }
        true
    }

    pub(crate) fn bring_online(&mut self, affinity: u32) -> bool {
        if affinity >= self.cpu_count || affinity >= 64 {
            return false;
        }
        self.online_mask |= 1u64 << affinity;
        true
    }

    pub(crate) fn route_external(&mut self, target_mask: u64) {
        self.external_pending |= target_mask & self.online_mask;
    }
}

#[derive(Clone, Copy)]
pub(crate) struct ExclusiveMonitor {
    pub(crate) valid: bool,
    pub(crate) address: u64,
    pub(crate) size: u8,
    pub(crate) owner: u32,
}

impl ExclusiveMonitor {
    pub(crate) const fn reset() -> Self {
        Self {
            valid: false,
            address: 0,
            size: 0,
            owner: 0,
        }
    }

    pub(crate) fn reserve(&mut self, address: u64, size: u8, owner: u32) {
        self.valid = true;
        self.address = address;
        self.size = size;
        self.owner = owner;
    }

    pub(crate) fn succeeds(&self, address: u64, size: u8, owner: u32) -> bool {
        self.valid && self.address == address && self.size == size && self.owner == owner
    }

    pub(crate) fn clear_on_store(&mut self, address: u64, size: u8) {
        if self.valid
            && self.address < address.saturating_add(u64::from(size))
            && address < self.address.saturating_add(u64::from(self.size))
        {
            self.valid = false;
        }
    }
}

pub(crate) type PauthBoundary = PauthState;

#[derive(Clone, Copy)]
pub(crate) struct GuestCpuState {
    pub(crate) x: [u64; 31],
    pub(crate) sp: u64,
    pub(crate) sp_el: [u64; 4],
    pub(crate) pc: u64,
    pub(crate) pstate: u32,
    pub(crate) current_el: ExceptionLevel,
    pub(crate) sys: SystemRegisters,
    pub(crate) pending_exception: Option<GuestException>,
    pub(crate) exception_target: Option<ExceptionLevel>,
    pub(crate) exception_from_lower_el: bool,
    pub(crate) exception_vector: u64,
    pub(crate) affinity: u32,
    pub(crate) mmu: VfMmu,
    pub(crate) timer: GenericTimer,
    pub(crate) virtual_timer: GenericTimer,
    pub(crate) smp: SmpState,
    pub(crate) exclusive: ExclusiveMonitor,
    pub(crate) pauth: PauthBoundary,
    pub(crate) waiting: bool,
    pub(crate) retired: u64,
    pub(crate) platform: crate::platform::PlatformState,
}

impl GuestCpuState {
    pub(crate) fn reset(affinity: u32) -> Self {
        Self {
            x: [0; 31],
            sp: 0,
            sp_el: [0; 4],
            pc: 0,
            pstate: mode_for_el(ExceptionLevel::El1),
            current_el: ExceptionLevel::El1,
            sys: SystemRegisters::reset(),
            pending_exception: None,
            exception_target: None,
            exception_from_lower_el: false,
            exception_vector: 0,
            affinity,
            mmu: VfMmu::disabled(),
            timer: GenericTimer::reset(),
            virtual_timer: GenericTimer::reset(),
            smp: SmpState::reset(),
            exclusive: ExclusiveMonitor::reset(),
            pauth: PauthBoundary::reset(),
            waiting: false,
            retired: 0,
            platform: crate::platform::PlatformState::reset(),
        }
    }

    pub(crate) fn set_exception_level(&mut self, value: u8) -> bool {
        let Some(level) = ExceptionLevel::from_u8(value) else {
            return false;
        };
        self.sp_el[self.active_sp_index()] = self.sp;
        self.current_el = level;
        self.pstate = (self.pstate & !PSTATE_MODE_MASK) | mode_for_el(level);
        self.sp = self.sp_el[level as usize];
        true
    }

    pub(crate) fn raise(&mut self, exception: GuestException) {
        if self.pending_exception.is_some() {
            return;
        }
        let mut exception = exception;
        exception.syndrome = exception_syndrome(
            exception.kind,
            self.current_el,
            exception.syndrome,
        );
        let target = if self.current_el == ExceptionLevel::El0 {
            ExceptionLevel::El1
        } else {
            self.current_el
        };
        self.write_exception_bank(target, self.pstate, exception);
        self.exception_target = Some(target);
        self.exception_from_lower_el = self.current_el != target;
        self.pending_exception = Some(exception);
    }

    fn write_exception_bank(
        &mut self,
        target: ExceptionLevel,
        saved_pstate: u32,
        exception: GuestException,
    ) {
        let asynchronous=matches!(exception.kind, ExceptionKind::TimerInterrupt |
            ExceptionKind::ExternalInterrupt | ExceptionKind::FiqInterrupt);
        match target {
            ExceptionLevel::El0 => {}
            ExceptionLevel::El1 => {
                self.sys.spsr_el1 = u64::from(saved_pstate);
                if !asynchronous { self.sys.esr_el1 = exception.syndrome; self.sys.far_el1 = exception.far; }
                self.sys.elr_el1 = exception.pc;
            }
            ExceptionLevel::El2 => {
                self.sys.spsr_el2 = u64::from(saved_pstate);
                if !asynchronous { self.sys.esr_el2 = exception.syndrome; self.sys.far_el2 = exception.far; }
                self.sys.elr_el2 = exception.pc;
            }
            ExceptionLevel::El3 => {
                self.sys.spsr_el3 = u64::from(saved_pstate);
                if !asynchronous { self.sys.esr_el3 = exception.syndrome; self.sys.far_el3 = exception.far; }
                self.sys.elr_el3 = exception.pc;
            }
        }
    }

    fn exception_bank(&self, level: ExceptionLevel) -> (u64, u64, u64) {
        match level {
            ExceptionLevel::El0 => (0, 0, 0),
            ExceptionLevel::El1 => (
                self.sys.spsr_el1,
                self.sys.elr_el1,
                self.sys.vbar_el1,
            ),
            ExceptionLevel::El2 => (
                self.sys.spsr_el2,
                self.sys.elr_el2,
                self.sys.vbar_el2,
            ),
            ExceptionLevel::El3 => (
                self.sys.spsr_el3,
                self.sys.elr_el3,
                self.sys.vbar_el3,
            ),
        }
    }

    fn active_sp_index(&self) -> usize {
        if self.current_el == ExceptionLevel::El0 || self.pstate & 1 == 0 {
            ExceptionLevel::El0 as usize
        } else {
            self.current_el as usize
        }
    }

    fn exception_offset(kind: ExceptionKind, from: ExceptionLevel, saved_pstate: u32) -> u64 {
        let synchronous = if from == ExceptionLevel::El0 {
            0x400
        } else if saved_pstate & 1 != 0 {
            0x200
        } else {
            0
        };
        match kind {
            ExceptionKind::TimerInterrupt | ExceptionKind::ExternalInterrupt => synchronous + 0x80,
            ExceptionKind::FiqInterrupt => synchronous + 0x100,
            _ => synchronous,
        }
    }

    pub(crate) fn take_pending_exception(&mut self) -> Option<GuestException> {
        let exception = self.pending_exception?;
        if exception.kind == ExceptionKind::GuestHalt {
            return Some(exception);
        }
        let old_level = self.current_el;
        let target = self.exception_target.unwrap_or(if old_level == ExceptionLevel::El0 {
            ExceptionLevel::El1
        } else {
            old_level
        });
        let saved_pstate = self.pstate;
        self.sp_el[self.active_sp_index()] = self.sp;
        self.write_exception_bank(target, saved_pstate, exception);
        self.current_el = target;
        self.pstate = (saved_pstate & !PSTATE_MODE_MASK)
            | mode_for_el(target)
            | PSTATE_D
            | PSTATE_A
            | PSTATE_I
            | PSTATE_F;
        self.sp = self.sp_el[target as usize];
        let (_, _, vector_base) = self.exception_bank(target);
        self.exception_vector = (vector_base & !0x7ff)
            .wrapping_add(Self::exception_offset(exception.kind, old_level, saved_pstate));
        self.pc = self.exception_vector;
        self.pending_exception = None;
        self.exception_target = None;
        self.exception_from_lower_el = false;
        Some(exception)
    }

    pub(crate) fn state_valid(&self) -> bool {
        let mode_valid = match self.current_el {
            ExceptionLevel::El0 => self.pstate & PSTATE_MODE_MASK == 0,
            ExceptionLevel::El1 => matches!(self.pstate & PSTATE_MODE_MASK, 4 | 5),
            ExceptionLevel::El2 => matches!(self.pstate & PSTATE_MODE_MASK, 8 | 9),
            ExceptionLevel::El3 => matches!(self.pstate & PSTATE_MODE_MASK, 12 | 13),
        };
        mode_valid
            && self
                .exception_target
                .map_or(self.pending_exception.is_none(), |target| {
                    self.pending_exception.is_some() && target as u8 <= 3
                })
            && (!self.exception_from_lower_el
                || self
                    .exception_target
                    .is_some_and(|target| (self.current_el as u8) < target as u8))
    }

    pub(crate) fn read_sysreg(&mut self, reg: SystemRegister) -> Result<u64, SysRegFault> {
        if matches!(reg, SystemRegister::IdAa64Zfr0El1 | SystemRegister::IdAa64Isar0El1) {
            return if self.current_el==ExceptionLevel::El1 && self.sys.hcr_el2==0 && self.sys.scr_el3==0 {
                Ok(0)
            } else { Err(SysRegFault::Unknown) };
        }
        if reg==SystemRegister::PlatformOverride {
            return if self.platform.profile==crate::platform::PROFILE_IRQ_COMPAT_V1 && self.current_el==ExceptionLevel::El1 && self.sys.hcr_el2==0 && self.sys.scr_el3==0 {
                Ok(self.platform.override_value)
            } else { Err(SysRegFault::Unknown) };
        }
        if reg == SystemRegister::TpidrEl1 && self.current_el == ExceptionLevel::El0 {
            return Err(SysRegFault::Undefined);
        }
        if (self.current_el as u8) < reg.minimum_el() as u8 {
            return Err(SysRegFault::Privilege);
        }
        match reg {
            SystemRegister::PlatformOverride | SystemRegister::IdAa64Zfr0El1 | SystemRegister::IdAa64Isar0El1 => unreachable!(),
            SystemRegister::TpidrEl0 => Ok(self.sys.tpidr_el0),
            SystemRegister::TpidrroEl0 => Ok(self.sys.tpidrro_el0),
            SystemRegister::TpidrEl1 => Ok(self.sys.tpidr_el1),
            SystemRegister::SctlrEl1 => Ok(self.sys.sctlr_el1),
            SystemRegister::Ttbr0El1 => Ok(self.sys.ttbr0_el1),
            SystemRegister::Ttbr1El1 => Ok(self.sys.ttbr1_el1),
            SystemRegister::TcrEl1 => Ok(self.sys.tcr_el1),
            SystemRegister::MairEl1 => Ok(self.sys.mair_el1),
            SystemRegister::VbarEl1 => Ok(self.sys.vbar_el1),
            SystemRegister::EsrEl1 => Ok(self.sys.esr_el1),
            SystemRegister::FarEl1 => Ok(self.sys.far_el1),
            SystemRegister::ElrEl1 => Ok(self.sys.elr_el1),
            SystemRegister::SpsrEl1 => Ok(self.sys.spsr_el1),
            SystemRegister::CntfrqEl0 => Ok(self.timer.frequency),
            SystemRegister::CntpctEl0 => Ok(self.timer.counter),
            SystemRegister::CntpCtlEl0 => Ok(self.timer.ctl),
            SystemRegister::CntpCvalEl0 => Ok(self.timer.cval),
            SystemRegister::CurrentEl => Ok(u64::from(self.current_el as u8) << 2),
            SystemRegister::IdAa64Mmfr0El1 => Ok(self.sys.id_aa64mmfr0_el1),
            SystemRegister::IdAa64Isar1El1 => Ok(self.sys.id_aa64isar1_el1),
            SystemRegister::CntvctEl0 => Ok(self.virtual_timer.counter),
            SystemRegister::CntvCtlEl0 => Ok(self.virtual_timer.ctl),
            SystemRegister::CntvCvalEl0 => Ok(self.virtual_timer.cval),
            SystemRegister::CntpTvalEl0 => Ok(self.timer.cval.saturating_sub(self.timer.counter)),
            SystemRegister::HcrEl2 => Ok(self.sys.hcr_el2),
            SystemRegister::CnthctlEl2 => Ok(self.sys.cnthctl_el2),
            SystemRegister::VbarEl2 => Ok(self.sys.vbar_el2),
            SystemRegister::EsrEl2 => Ok(self.sys.esr_el2),
            SystemRegister::FarEl2 => Ok(self.sys.far_el2),
            SystemRegister::ElrEl2 => Ok(self.sys.elr_el2),
            SystemRegister::SpsrEl2 => Ok(self.sys.spsr_el2),
            SystemRegister::ScrEl3 => Ok(self.sys.scr_el3),
            SystemRegister::VbarEl3 => Ok(self.sys.vbar_el3),
            SystemRegister::EsrEl3 => Ok(self.sys.esr_el3),
            SystemRegister::FarEl3 => Ok(self.sys.far_el3),
            SystemRegister::ElrEl3 => Ok(self.sys.elr_el3),
            SystemRegister::SpsrEl3 => Ok(self.sys.spsr_el3),
        }
    }

    pub(crate) fn write_sysreg(
        &mut self,
        reg: SystemRegister,
        value: u64,
    ) -> Result<(), SysRegFault> {
        if reg==SystemRegister::PlatformOverride {
            if self.platform.profile!=crate::platform::PROFILE_IRQ_COMPAT_V1 || self.current_el!=ExceptionLevel::El1 || self.sys.hcr_el2!=0 || self.sys.scr_el3!=0 {
                return Err(SysRegFault::Unknown);
            }
            return if self.platform.configure(self.platform.profile,value) { Ok(()) }
                else { Err(SysRegFault::InvalidValue) };
        }
        if self.current_el == ExceptionLevel::El0
            && matches!(reg, SystemRegister::TpidrEl1 | SystemRegister::TpidrroEl0)
        {
            return Err(SysRegFault::Undefined);
        }
        if (self.current_el as u8) < reg.minimum_el() as u8 {
            return Err(SysRegFault::Privilege);
        }
        match reg {
            SystemRegister::PlatformOverride => unreachable!(),
            SystemRegister::TpidrEl0 => self.sys.tpidr_el0 = value,
            SystemRegister::TpidrroEl0 => self.sys.tpidrro_el0 = value,
            SystemRegister::TpidrEl1 => self.sys.tpidr_el1 = value,
            SystemRegister::SctlrEl1 => {
                let old = self.sys.sctlr_el1;
                self.sys.sctlr_el1 = value;
                if self.sync_mmu().is_err() {
                    self.sys.sctlr_el1 = old;
                    let _ = self.sync_mmu();
                    return Err(SysRegFault::InvalidValue);
                }
            }
            SystemRegister::Ttbr0El1 => {
                if value & 0xfff != 0 {
                    return Err(SysRegFault::InvalidValue);
                }
                let old = self.sys.ttbr0_el1;
                self.sys.ttbr0_el1 = value;
                if self.sys.sctlr_el1 & SCTLR_M != 0 {
                    if self.sync_mmu().is_err() {
                        self.sys.ttbr0_el1 = old;
                        let _ = self.sync_mmu();
                        return Err(SysRegFault::InvalidValue);
                    }
                }
            }
            SystemRegister::Ttbr1El1 => {
                if value & 0xfff != 0 {
                    return Err(SysRegFault::InvalidValue);
                }
                let old = self.sys.ttbr1_el1;
                self.sys.ttbr1_el1 = value;
                if self.sys.sctlr_el1 & SCTLR_M != 0 && self.sync_mmu().is_err() {
                    self.sys.ttbr1_el1 = old;
                    let _ = self.sync_mmu();
                    return Err(SysRegFault::InvalidValue);
                }
            }
            SystemRegister::TcrEl1 => {
                let old = self.sys.tcr_el1;
                self.sys.tcr_el1 = value;
                if self.sys.sctlr_el1 & SCTLR_M != 0 && self.sync_mmu().is_err() {
                    self.sys.tcr_el1 = old;
                    let _ = self.sync_mmu();
                    return Err(SysRegFault::InvalidValue);
                }
            }
            SystemRegister::MairEl1 => self.sys.mair_el1 = value,
            SystemRegister::VbarEl1 => self.sys.vbar_el1 = value & !0x7ff,
            SystemRegister::EsrEl1 => self.sys.esr_el1 = value,
            SystemRegister::FarEl1 => self.sys.far_el1 = value,
            SystemRegister::ElrEl1 => self.sys.elr_el1 = value,
            SystemRegister::SpsrEl1 => self.sys.spsr_el1 = value,
            SystemRegister::CntfrqEl0
            | SystemRegister::CntpctEl0
            | SystemRegister::CurrentEl
            | SystemRegister::IdAa64Mmfr0El1
            | SystemRegister::IdAa64Isar1El1
            | SystemRegister::IdAa64Zfr0El1
            | SystemRegister::IdAa64Isar0El1
            | SystemRegister::CntvctEl0 => {
                return Err(SysRegFault::ReadOnly)
            }
            SystemRegister::CntpCtlEl0 => {
                // ISTATUS is read-only and is recomputed from counter/CVAL;
                // only ENABLE and IMASK are writable through this register.
                self.timer.ctl = value & (CNTP_CTL_ENABLE | CNTP_CTL_IMASK);
                if self.timer.pending() {
                    self.timer.ctl |= CNTP_CTL_ISTATUS;
                }
                self.sys.cntp_ctl_el0 = self.timer.ctl;
            }
            SystemRegister::CntpCvalEl0 => {
                self.timer.cval = value;
                self.sys.cntp_cval_el0 = value;
            }
            SystemRegister::CntvCtlEl0 => {
                self.virtual_timer.ctl = value & (CNTP_CTL_ENABLE | CNTP_CTL_IMASK);
                if self.virtual_timer.pending() {
                    self.virtual_timer.ctl |= CNTP_CTL_ISTATUS;
                }
                self.sys.cntv_ctl_el0 = self.virtual_timer.ctl;
            }
            SystemRegister::CntvCvalEl0 => {
                self.virtual_timer.cval = value;
                self.sys.cntv_cval_el0 = value;
            }
            SystemRegister::CntpTvalEl0 => {
                self.timer.cval = self.timer.counter.wrapping_add(value);
                self.sys.cntp_cval_el0 = self.timer.cval;
                self.sys.cntp_tval_el0 = value;
            }
            SystemRegister::HcrEl2 => self.sys.hcr_el2 = value,
            SystemRegister::CnthctlEl2 => self.sys.cnthctl_el2 = value,
            SystemRegister::VbarEl2 => self.sys.vbar_el2 = value & !0x7ff,
            SystemRegister::EsrEl2 => self.sys.esr_el2 = value,
            SystemRegister::FarEl2 => self.sys.far_el2 = value,
            SystemRegister::ElrEl2 => self.sys.elr_el2 = value,
            SystemRegister::SpsrEl2 => self.sys.spsr_el2 = value,
            SystemRegister::ScrEl3 => self.sys.scr_el3 = value,
            SystemRegister::VbarEl3 => self.sys.vbar_el3 = value & !0x7ff,
            SystemRegister::EsrEl3 => self.sys.esr_el3 = value,
            SystemRegister::FarEl3 => self.sys.far_el3 = value,
            SystemRegister::ElrEl3 => self.sys.elr_el3 = value,
            SystemRegister::SpsrEl3 => self.sys.spsr_el3 = value,
        }
        Ok(())
    }

    fn sync_mmu(&mut self) -> Result<(), ()> {
        if self.sys.sctlr_el1 & SCTLR_M == 0 {
            self.mmu.disable();
            return Ok(());
        }
        let asid = (self.sys.ttbr0_el1 >> 48) as u16;
        if !self.mmu.configure_tcr(
            self.sys.ttbr0_el1,
            self.sys.ttbr1_el1,
            self.sys.tcr_el1,
            asid,
        ) {
            return Err(());
        }
        Ok(())
    }

    pub(crate) fn advance_counter(&mut self, ticks: u64) {
        self.timer.advance(ticks);
        self.virtual_timer.advance(ticks);
        self.sys.cntpct_el0 = self.timer.counter;
        self.sys.cntp_ctl_el0 = self.timer.ctl;
        self.sys.cntvct_el0 = self.virtual_timer.counter;
        self.sys.cntv_ctl_el0 = self.virtual_timer.ctl;
        self.sys.cntp_tval_el0 = self.timer.cval.saturating_sub(self.timer.counter);
    }

    pub(crate) fn poll_interrupt(&mut self) -> bool {
        if self.pending_exception.is_some() {
            return false;
        }
        if (self.platform.irq || self.platform.fiq || self.timer.pending() || self.virtual_timer.pending() || self.smp.external_pending!=0)
            && (self.current_el as u8>1 || self.sys.hcr_el2&0x18!=0 || self.sys.scr_el3&6!=0) {
            self.raise(GuestException {kind:ExceptionKind::SystemRegisterTrap,instruction:0,
                syndrome:0,far:0,pc:self.pc});return true;
        }
        if self.platform.fiq && self.platform.fiq_enabled() && self.pstate & PSTATE_F == 0 {
            self.raise(GuestException { kind: ExceptionKind::FiqInterrupt,
                instruction:0,syndrome:0,far:0,pc:self.pc });return true;
        }
        if self.pstate & PSTATE_I != 0 || !self.platform.irq_enabled() { return false; }
        if self.timer.pending() || self.virtual_timer.pending() {
            self.raise(GuestException {
                kind: ExceptionKind::TimerInterrupt,
                instruction: 0,
                syndrome: 0,
                far: 0,
                pc: self.pc,
            });
            return true;
        }
        let bit = 1u64 << self.affinity;
        if self.platform.irq || self.smp.external_pending & bit != 0 {
            self.smp.external_pending &= !bit;
            self.raise(GuestException {
                kind: ExceptionKind::ExternalInterrupt,
                instruction: 0,
                syndrome: 0,
                far: 0,
                pc: self.pc,
            });
            return true;
        }
        false
    }

    /// Commit a latched asynchronous interrupt at the current instruction
    /// boundary.  `poll_interrupt` deliberately only records the source so
    /// callers can inspect it; this helper performs the architectural entry
    /// (SPSR/ELR save, target EL, interrupt masking, and vector selection).
    /// Synchronous exceptions and GuestHalt are left for the existing
    /// explicit `take_pending_exception` path.
    ///
    /// Design note: only asynchronous exceptions (timer/external) are
    /// auto-committed here.  Synchronous exceptions (DataAbort,
    /// TranslationFault, etc.) remain latched so the caller can inspect
    /// ESR/FAR/instruction before deciding whether to enter the vector.
    /// This is the correct boundary for a bounded diagnostic runner: the
    /// architectural state is frozen at the faulting instruction and the
    /// host can report the exact syndrome without the guest handler
    /// overwriting ESR/ELR.
    fn commit_pending_interrupt(&mut self) -> Option<GuestException> {
        match self.pending_exception.map(|exception| exception.kind) {
            Some(ExceptionKind::TimerInterrupt | ExceptionKind::ExternalInterrupt | ExceptionKind::FiqInterrupt) => {
                self.take_pending_exception()
            }
            _ => None,
        }
    }

    pub(crate) fn eret(&mut self) -> Result<(), ExceptionKind> {
        let level = self.current_el;
        if level == ExceptionLevel::El0 {
            return Err(ExceptionKind::PrivilegedInstruction);
        }
        let (saved_pstate, saved_pc, _) = self.exception_bank(level);
        let restored_pstate = saved_pstate as u32;
        let restored_el = level_for_mode(restored_pstate)
            .ok_or(ExceptionKind::UndefinedInstruction)?;
        self.sp_el[self.active_sp_index()] = self.sp;
        self.pstate = restored_pstate;
        self.pc = saved_pc;
        self.current_el = restored_el;
        self.sp = self.sp_el[restored_el as usize];
        Ok(())
    }

    fn mmu_address<B: GuestBus>(
        &mut self,
        bus: &mut B,
        address: u64,
        size: usize,
        access: Access,
    ) -> Result<u64, ExceptionKind> {
        if size > 1 && address & (size as u64 - 1) != 0 && self.sys.sctlr_el1 & SCTLR_A != 0 {
            return Err(ExceptionKind::AlignmentFault);
        }
        let translation = self
            .mmu
            .translate(address, access, self.current_el, |physical| {
                bus.read(physical, 8, Access::Read).ok()
            })
            .map_err(map_mmu_fault)?;
        Ok(translation.pa)
    }

    fn fetch32<B: GuestBus>(&mut self, bus: &mut B) -> Result<u32, ExceptionKind> {
        if self.pc & 3 != 0 {
            return Err(ExceptionKind::AlignmentFault);
        }
        let physical = self.mmu_address(bus, self.pc, 4, Access::Execute)?;
        bus.read(physical, 4, Access::Execute)
            .map(|value| value as u32)
            .map_err(|_| ExceptionKind::InstructionAbort)
    }

    fn scalar_memory<B: GuestBus>(&mut self, bus: &mut B, word: u32)
        -> Result<(), (ExceptionKind, u64)> {
        let (size_code, opc) = (word >> 30, (word >> 22) & 3);
        let (rn, rt) = ((word >> 5) & 31, word & 31);
        let register_offset = word & 0x3b200c00 == 0x38200800;
        let writeback = word & 0x3b200400 == 0x38000400;
        let option = (word >> 13) & 7;
        if (writeback && rn != 31 && rn == rt) ||
            (register_offset && option & 2 == 0) || word & (1 << 26) != 0 ||
            (opc >= 2 && (size_code == 3 || (opc == 3 && size_code == 2))) {
            return Err((ExceptionKind::UndefinedInstruction, self.pc));
        }
        let endian = if self.current_el == ExceptionLevel::El0 {24} else {25};
        if self.current_el as u8 > ExceptionLevel::El1 as u8 ||
            self.sys.hcr_el2 != 0 || self.sys.scr_el3 != 0 ||
            self.sys.sctlr_el1 & (1 << endian) != 0 ||
            (self.sys.sctlr_el1 & SCTLR_M != 0 && !self.mmu.enabled) {
            return Err((ExceptionKind::SystemRegisterTrap, self.pc));
        }
        let size = 1usize << size_code;
        let base = self.read_reg(rn, true);
        let sa = if self.current_el == ExceptionLevel::El0 {16} else {8};
        if rn == 31 && self.sys.sctlr_el1 & sa != 0 && base & 15 != 0 {
            return Err((ExceptionKind::SpAlignmentFault, base));
        }
        let offset = if register_offset {
            let raw = self.read_reg((word >> 16) & 31, false);
            let extended = match option {
                2 => u64::from(raw as u32),
                6 => (raw as u32 as i32 as i64) as u64,
                _ => raw,
            };
            extended << if word & (1 << 12) != 0 {size_code} else {0}
        } else if word & 0x3b200c00 == 0x38000000 || writeback {
            ((((word >> 12) & 511) as i64) << 55 >> 55) as u64
        } else {u64::from((word >> 10) & 4095) << size_code};
        let updated_base = base.wrapping_add(offset);
        let address = if writeback && word & (1 << 11) == 0 {base} else {updated_base};
        if address & (size as u64 - 1) != 0 {
            // Device-nGnRnE when MMU-off. Translated A=0 requires memory
            // attributes and a spanning transaction, neither exposed yet.
            let kind = if !self.mmu.enabled || self.sys.sctlr_el1 & SCTLR_A != 0 {
                ExceptionKind::AlignmentFault
            } else {ExceptionKind::SystemRegisterTrap};
            return Err((kind, address));
        }
        let access = if opc == 0 {Access::Write} else {Access::Read};
        // Natural alignment and <=8 bytes mean no supported page crossing.
        let physical = self.mmu_address(bus, address, size, access).map_err(|kind|(kind,address))?;
        if opc == 0 {
            let mask = if size == 8 {u64::MAX} else {(1u64 << (size * 8)) - 1};
            bus.write(physical, size, self.read_reg(rt, false) & mask, access).map_err(|kind|(kind,address))?;
            self.exclusive.clear_on_store(physical, size as u8);
        } else {
            let value = bus.read(physical, size, access).map_err(|kind|(kind,address))?;
            let value = if opc >= 2 {sign_extend(value, (size * 8) as u32) as u64} else {value};
            self.write_reg(rt, value, false, opc == 2 || size == 8);
        }
        if writeback { self.write_reg(rn, updated_base, true, true); }
        self.pc = self.pc.wrapping_add(4);
        Ok(())
    }

    fn pair_memory<B: GuestBus>(&mut self, bus: &mut B, word: u32)
        -> Result<(), (ExceptionKind, u64)> {
        let (opc, mode, load) = (word >> 30, (word >> 23) & 3, word & (1 << 22) != 0);
        let (rt, rn, rt2) = (word & 31, (word >> 5) & 31, (word >> 10) & 31);
        let wback = mode != 2;
        if word & (1 << 26) != 0 || !matches!(opc, 0 | 2) || mode == 0 ||
            (wback && rn != 31 && (rn == rt || rn == rt2)) || (load && rt == rt2) {
            return Err((ExceptionKind::UndefinedInstruction, self.pc));
        }
        let endian = if self.current_el == ExceptionLevel::El0 { 24 } else { 25 };
        if self.current_el as u8 > ExceptionLevel::El1 as u8 || self.mmu.enabled ||
            self.sys.sctlr_el1 & (SCTLR_M | (1 << endian)) != 0 ||
            self.sys.hcr_el2 != 0 || self.sys.scr_el3 != 0 {
            return Err((ExceptionKind::SystemRegisterTrap, self.pc));
        }
        let size = if opc == 2 { 8usize } else { 4 };
        let raw_base = self.read_reg(rn, true);
        let sa = if self.current_el == ExceptionLevel::El0 { 16 } else { 8 };
        if rn == 31 && self.sys.sctlr_el1 & sa != 0 && raw_base & 15 != 0 {
            return Err((ExceptionKind::SpAlignmentFault, raw_base));
        }
        let signed_imm = (((word >> 15) & 127) as i8) << 1 >> 1;
        let offset = (i64::from(signed_imm) * size as i64) as u64;
        let updated_base = raw_base.wrapping_add(offset);
        let address = if mode == 1 { raw_base } else { updated_base };
        // This bounded MMU-off/HCR=0 regime is Device-nGnRnE. A=0 does
        // not permit unaligned Device accesses, even to caller-owned RAM.
        if address & (size as u64 - 1) != 0 {
            return Err((ExceptionKind::AlignmentFault, address));
        }
        let source = [self.read_reg(rt, false), self.read_reg(rt2, false)];
        let (ram, base) = bus.pair_ram().ok_or((ExceptionKind::SystemRegisterTrap, self.pc))?;
        let mut indices = [0usize; 2];
        for (element, index) in indices.iter_mut().enumerate() {
            let at = address.checked_add((element * size) as u64)
                .ok_or((ExceptionKind::DataAbort, address.wrapping_add(size as u64)))?;
            *index = at.checked_sub(base).and_then(|v| usize::try_from(v).ok())
                .filter(|v| ram.len() >= size && *v <= ram.len() - size)
                .ok_or((ExceptionKind::DataAbort, at))?;
        }
        if load {
            let values = [read_width(ram, indices[0], size).unwrap(),
                          read_width(ram, indices[1], size).unwrap()];
            self.write_reg(rt, values[0], false, size == 8);
            self.write_reg(rt2, values[1], false, size == 8);
        } else {
            for element in 0..2 {
                let written = write_width(ram, indices[element], size, source[element]);
                debug_assert!(written);
                self.exclusive.clear_on_store(address + (element * size) as u64, size as u8);
            }
        }
        if wback { self.write_reg(rn, updated_base, true, true); }
        self.pc = self.pc.wrapping_add(4);
        Ok(())
    }

    fn read_reg(&self, index: u32, sp_allowed: bool) -> u64 {
        if index == 31 {
            if sp_allowed {
                self.sp
            } else {
                0
            }
        } else {
            self.x[index as usize]
        }
    }

    fn write_reg(&mut self, index: u32, value: u64, sp_allowed: bool, wide: bool) {
        let value = if wide { value } else { value as u32 as u64 };
        if index == 31 {
            if sp_allowed {
                self.sp = value;
            }
        } else {
            self.x[index as usize] = value;
        }
    }

    fn set_nzcv(&mut self, value: u64, wide: bool, carry: bool, overflow: bool) {
        let width = if wide { 64 } else { 32 };
        let mask = if wide { u64::MAX } else { u64::from(u32::MAX) };
        let value = value & mask;
        let sign = 1u64 << (width - 1);
        self.pstate &= !(PSTATE_N | PSTATE_Z | PSTATE_C | PSTATE_V);
        if value & sign != 0 {
            self.pstate |= PSTATE_N;
        }
        if value == 0 {
            self.pstate |= PSTATE_Z;
        }
        if carry {
            self.pstate |= PSTATE_C;
        }
        if overflow {
            self.pstate |= PSTATE_V;
        }
    }

    fn condition_holds(&self, condition: u32) -> bool {
        let n=self.pstate&PSTATE_N!=0;let z=self.pstate&PSTATE_Z!=0;
        let c=self.pstate&PSTATE_C!=0;let v=self.pstate&PSTATE_V!=0;
        let base=match condition>>1 {0=>z,1=>c,2=>n,3=>v,4=>c&&!z,5=>n==v,6=>n==v&&!z,_=>true};
        if condition&1!=0 && condition!=15 {!base} else {base}
    }

    fn execute_one<B: GuestBus>(&mut self, bus: &mut B) -> StepResult {
        let pc = self.pc;
        let word = match self.fetch32(bus) {
            Ok(value) => value,
            Err(kind) => {
                self.raise(GuestException {
                    kind,
                    instruction: 0,
                    syndrome: 0,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(kind);
            }
        };
        let rd = word & 31;
        let rn = (word >> 5) & 31;
        let wide = word & (1 << 31) != 0;

        // The same software PAC implementation serves the EFI native-code
        // dispatcher and this architectural path. Existing MMU/system-register
        // semantics below retain ownership of SCTLR/TCR/ID access here.
        let syskey = (word >> 5) & 0x7fff;
        if !matches!(syskey, 0x4080 | 0x4102 | 0x4031)
            || word & 0xffc00000 != 0xd5000000
        {
            let mut context = PauthContext::new(self.x, self.sp, self.pc,
                self.sys.sctlr_el1, self.sys.tcr_el1, self.pauth, self.current_el as u32);
            if let Some(result) = pauth::step(&mut context, word) {
                if result.is_ok() {
                    self.x = context.x; self.sp = context.sp; self.pc = context.pc;
                    self.pauth = context.state();
                    return StepResult::Continue;
                }
                self.raise(GuestException { kind: ExceptionKind::UndefinedInstruction,
                    instruction: word, syndrome: word as u64, far: pc, pc });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
        }

        if word == 0xd503201f {
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        if word & 0xffe0001f == 0xd4400000 {
            if (word >> 5) & 0xffff == 0 {
                self.pc = pc.wrapping_add(4);
                return StepResult::Halt;
            }
            self.raise(GuestException {
                kind: ExceptionKind::UndefinedInstruction,
                instruction: word,
                syndrome: word as u64,
                far: pc,
                pc,
            });
            return StepResult::Exception(ExceptionKind::UndefinedInstruction);
        }
        if word == 0xd503207f || word == 0xd503205f {
            if self.current_el == ExceptionLevel::El0 {
                self.raise(GuestException {
                    kind: ExceptionKind::PrivilegedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::PrivilegedInstruction);
            }
            self.pc = pc.wrapping_add(4);
            self.waiting = true;
            return StepResult::Wait;
        }
        // DAIF and SPSel are architectural state updates, not generic system
        // register accesses.  They are accepted at EL1+ and rejected at EL0.
        if word & 0xffff_f0ff == 0xd503_40df
            || word & 0xffff_f0ff == 0xd503_40ff
        {
            if self.current_el == ExceptionLevel::El0 {
                self.raise(GuestException {
                    kind: ExceptionKind::PrivilegedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::PrivilegedInstruction);
            }
            let mask = u32::from(((word >> 8) & 0xf) as u8) << 6;
            if word & 0xff == 0xdf {
                self.pstate |= mask;
            } else {
                self.pstate &= !mask;
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        if word & !0x100 == 0xd500_40bf {
            if self.current_el == ExceptionLevel::El0 {
                self.raise(GuestException {
                    kind: ExceptionKind::PrivilegedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::PrivilegedInstruction);
            }
            self.sp_el[self.active_sp_index()] = self.sp;
            if word & 0x100 != 0 {
                self.pstate |= 1;
            } else {
                self.pstate &= !1;
            }
            self.sp = self.sp_el[self.active_sp_index()];
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        // The bounded TLB has no separate global/set-associative state, so
        // both VMALLE1 and ASIDE1 invalidate the complete local array.  This
        // preserves the architectural ordering boundary without pretending
        // to implement a host TLB flush.
        let tlbi_vmalle1 = word == 0xd508_871f;
        let tlbi_aside1 = word & 0xffff_fc1f == 0xd508_8740;
        if tlbi_vmalle1 || tlbi_aside1 {
            if self.current_el == ExceptionLevel::El0 {
                self.raise(GuestException {
                    kind: ExceptionKind::PrivilegedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::PrivilegedInstruction);
            }
            self.mmu.invalidate();
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        if word == 0xd69f03e0 {
            match self.eret() {
                Ok(()) => return StepResult::Continue,
                Err(kind) => {
                    self.raise(GuestException {
                        kind,
                        instruction: word,
                        syndrome: word as u64,
                        far: pc,
                        pc,
                    });
                    return StepResult::Exception(kind);
                }
            }
        }
        if word & 0xffe0001f == 0xd4000001 {
            self.raise(GuestException {
                kind: ExceptionKind::SupervisorCall,
                instruction: word,
                syndrome: word as u64,
                far: 0,
                pc,
            });
            return StepResult::Exception(ExceptionKind::SupervisorCall);
        }

        // Single-copy atomic instructions.  The reservation is recorded in
        // guest-physical space, after translation, so two virtual aliases of
        // one page cannot accidentally create two independent reservations.
        // Acquire/release variants share the same single-core ordering here;
        // DMB/DSB/ISB below are explicit architectural boundaries and retire
        // as ordered no-ops until the SMP scheduler supplies another core.
        let exclusive_class = word & 0x3fc0_7c00;
        let exclusive_load = exclusive_class == 0x0840_7c00;
        let exclusive_store = exclusive_class == 0x0800_7c00;
        if exclusive_load || exclusive_store {
            let size = if wide { 8usize } else { 4usize };
            let address = self.read_reg(rn, true);
            if address & (size as u64 - 1) != 0 {
                self.raise(GuestException {
                    kind: ExceptionKind::AlignmentFault,
                    instruction: word,
                    syndrome: access_syndrome(if exclusive_load {
                        Access::Read
                    } else {
                        Access::Write
                    }),
                    far: address,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::AlignmentFault);
            }
            let physical = match self.mmu_address(
                bus,
                address,
                size,
                if exclusive_load { Access::Read } else { Access::Write },
            ) {
                Ok(value) => value,
                Err(kind) => {
                    self.raise(GuestException {
                        kind,
                        instruction: word,
                        syndrome: access_syndrome(if exclusive_load {
                            Access::Read
                        } else {
                            Access::Write
                        }),
                        far: address,
                        pc,
                    });
                    return StepResult::Exception(kind);
                }
            };
            if exclusive_load {
                let value = match bus.read(physical, size, Access::Read) {
                    Ok(value) => value,
                    Err(kind) => {
                        self.raise(GuestException {
                            kind,
                            instruction: word,
                            syndrome: access_syndrome(Access::Read),
                            far: address,
                            pc,
                        });
                        return StepResult::Exception(kind);
                    }
                };
                self.write_reg(rd, value, false, wide);
                self.exclusive
                    .reserve(physical, size as u8, self.affinity);
            } else {
                let status = (word >> 16) & 31;
                let value = self.read_reg(rd, false);
                let succeeds = self
                    .exclusive
                    .succeeds(physical, size as u8, self.affinity);
                if succeeds {
                    if let Err(kind) = bus.write(physical, size, value, Access::Write) {
                        self.raise(GuestException {
                            kind,
                            instruction: word,
                            syndrome: access_syndrome(Access::Write),
                            far: address,
                            pc,
                        });
                        return StepResult::Exception(kind);
                    }
                }
                // A store-exclusive consumes the reservation whether it
                // succeeds or fails.  A normal store below uses the same
                // physical-address invalidation rule.
                self.exclusive.valid = false;
                self.write_reg(status, if succeeds { 0 } else { 1 }, false, false);
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // The architectural barrier encodings have no observable effect in a
        // single-core reference run, but accepting them is important: kernel
        // atomics routinely bracket exclusive sequences with these barriers.
        // The option field is intentionally ignored; the instruction still
        // retires in program order and never crosses the host ABI boundary.
        if word & 0xffff_f0ff == 0xd503_30bf
            || word & 0xffff_f0ff == 0xd503_309f
            || word & 0xffff_f0ff == 0xd503_30df
        {
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        if word & 0xffff_f0ff == 0xd503_305f {
            self.exclusive.valid = false;
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // MRS/MSR use the same system-register key. Unknown keys are a system
        // register trap, while EL0 access to an EL1 register is a privilege
        // fault.
        let mrs = word & 0xffe00000 == 0xd5200000;
        let msr = word & 0xffe00000 == 0xd5000000;
        if mrs || msr {
            let Some(reg) = SystemRegister::from_instruction(word) else {
                self.raise(GuestException {
                    kind: ExceptionKind::SystemRegisterTrap,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::SystemRegisterTrap);
            };
            let result = if mrs {
                self.read_sysreg(reg).map(|value| {
                    self.write_reg(rd, value, false, true);
                })
            } else {
                let value = self.read_reg(rd, false);
                self.write_sysreg(reg, value)
            };
            if let Err(fault) = result {
                let kind = if fault == SysRegFault::Undefined {
                    ExceptionKind::UndefinedInstruction
                } else if fault == SysRegFault::Privilege {
                    ExceptionKind::PrivilegedInstruction
                } else {
                    ExceptionKind::SystemRegisterTrap
                };
                self.raise(GuestException {
                    kind,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(kind);
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // Ordinary MADD/MSUB only; widened and high-half encodings stay gated.
        if word & 0x7fe00000 == 0x1b000000 {
            let product = self.read_reg(rn, false).wrapping_mul(self.read_reg((word >> 16) & 31, false));
            let addend = self.read_reg((word >> 10) & 31, false);
            let result = if word & (1 << 15) != 0 { addend.wrapping_sub(product) }
                else { addend.wrapping_add(product) };
            self.write_reg(rd, result, false, wide);
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // Conditional selection reads ZR for every register31 operand.
        if word & 0x3fe00800 == 0x1a800000 {
            let value = if self.condition_holds((word >> 12) & 15) {
                self.read_reg(rn, false)
            } else {
                let mut other = self.read_reg((word >> 16) & 31, false);
                if word & (1 << 30) != 0 { other = !other; }
                if word & (1 << 10) != 0 { other = other.wrapping_add(1); }
                other
            };
            self.write_reg(rd, value, false, wide);
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        if word&0x3fe00410==0x3a400000 {
            if self.condition_holds((word>>12)&15) {
                let right=if word&(1<<11)!=0 {u64::from((word>>16)&31)}
                    else {self.read_reg((word>>16)&31,false)};
                let (value,carry,overflow)=add_sub(self.read_reg(rn,false),right,word&(1<<30)!=0,wide);
                self.set_nzcv(value,wide,carry,overflow);
            } else {
                self.pstate=(self.pstate&!0xf0000000)|((word&15)<<28);
            }
            self.pc=pc.wrapping_add(4);return StepResult::Continue;
        }
        if word&0x7f800000==0x33000000 {
            let r=(word>>16)&63;let s=(word>>10)&63;
            if ((word>>22)&1)!=u32::from(wide) || (!wide && (r|s)&32!=0) {
                self.raise(GuestException {kind:ExceptionKind::UndefinedInstruction,
                    instruction:word,syndrome:word as u64,far:pc,pc});
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let width=if wide {64}else{32};
            let low=|bits:u32|u64::MAX>>(64-bits);
            let rotate=|x:u64|if wide{x.rotate_right(r)}else{u64::from((x as u32).rotate_right(r))};
            let wmask=rotate(low(s+1));let tmask=low((s.wrapping_sub(r)&(width-1))+1);
            let old=self.read_reg(rd,false);let source=self.read_reg(rn,false);
            let bottom=(old&!wmask)|(rotate(source)&wmask);
            self.write_reg(rd,(old&!tmask)|(bottom&tmask),false,wide);
            self.pc=pc.wrapping_add(4);return StepResult::Continue;
        }
        if word&0x7f800000==0x53000000 {
            let r=(word>>16)&63;let s=(word>>10)&63;
            if ((word>>22)&1)!=u32::from(wide) || (!wide && (r|s)&32!=0) {
                self.raise(GuestException {kind:ExceptionKind::UndefinedInstruction,
                    instruction:word,syndrome:word as u64,far:pc,pc});
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            // Arm's rotate/write-mask/top-mask operation. Unlike logical
            // immediates, a full-width bitfield is valid. R31 is always ZR.
            let width=if wide {64}else{32};
            let low=|bits:u32|u64::MAX>>(64-bits);
            let rotate=|x:u64|if wide {x.rotate_right(r)}else{u64::from((x as u32).rotate_right(r))};
            let result=rotate(self.read_reg(rn,false)) & rotate(low(s+1)) & low((s.wrapping_sub(r)&(width-1))+1);
            self.write_reg(rd,result,false,wide);
            self.pc=pc.wrapping_add(4);return StepResult::Continue;
        }
        if word&0x1f800000==0x12000000 {
            let Some(mask)=logical_immediate(word) else {
                self.raise(GuestException {kind:ExceptionKind::UndefinedInstruction,
                    instruction:word,syndrome:word as u64,far:pc,pc});
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            };
            let op=(word>>29)&3;let input=self.read_reg(rn,false);
            let mut result=match op {1=>input|mask,2=>input^mask,_=>input&mask};
            if !wide {result&=0xffff_ffff;}
            self.write_reg(rd,result,op!=3,wide);
            if op==3 {
                let n=((result>>(if wide {63} else {31}))&1) as u32;
                self.pstate=(self.pstate&!0xf0000000)|(n<<31)|((u32::from(result==0))<<30);
            }
            self.pc=pc.wrapping_add(4);return StepResult::Continue;
        }
        // Logical shifted register. Register 31 is ZR in every position.
        if word & 0x1f000000 == 0x0a000000 {
            let op = (word >> 29) & 3;
            let shift = (word >> 22) & 3;
            let amount = (word >> 10) & 63;
            if !wide && amount >= 32 {
                self.raise(GuestException {
                    kind: ExceptionKind::UndefinedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let source = self.read_reg((word >> 16) & 31, false);
            let mut right = if wide {
                match shift {
                    0 => source << amount,
                    1 => source >> amount,
                    2 => ((source as i64) >> amount) as u64,
                    _ => source.rotate_right(amount),
                }
            } else {
                let source = source as u32;
                u64::from(match shift {
                    0 => source << amount,
                    1 => source >> amount,
                    2 => ((source as i32) >> amount) as u32,
                    _ => source.rotate_right(amount),
                })
            };
            if word & (1 << 21) != 0 { right = !right; }
            let left = self.read_reg(rn, false);
            let mut value = match op {
                1 => left | right,
                2 => left ^ right,
                _ => left & right,
            };
            if !wide { value = u64::from(value as u32); }
            self.write_reg(rd, value, false, wide);
            if op == 3 { self.set_nzcv(value, wide, false, false); }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        // LSLV/LSRV/ASRV/RORV: both sources are read before writing Rd.
        if word & 0x7fe0f000 == 0x1ac02000 {
            let shift = (word >> 10) & 3;
            let count = (self.read_reg((word >> 16) & 31, false) & if wide {63} else {31}) as u32;
            let source = self.read_reg(rn, false);
            let value = if wide {
                match shift {
                    0 => source << count,
                    1 => source >> count,
                    2 => ((source as i64) >> count) as u64,
                    _ => source.rotate_right(count),
                }
            } else {
                let source = source as u32;
                u64::from(match shift {
                    0 => source << count,
                    1 => source >> count,
                    2 => ((source as i32) >> count) as u32,
                    _ => source.rotate_right(count),
                })
            };
            self.write_reg(rd, value, false, wide);
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }
        // MOVZ/MOVK, 32- and 64-bit forms.
        let move_op = word & 0x7f800000;
        if move_op == 0x52800000 || move_op == 0x72800000 {
            let shift = ((word >> 21) & 3) * 16;
            if !wide && shift >= 32 {
                self.raise(GuestException {
                    kind: ExceptionKind::UndefinedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let mask = u64::from(0xffffu32) << shift;
            let immediate = u64::from((word >> 5) & 0xffff) << shift;
            let value = if move_op == 0x72800000 {
                (self.read_reg(rd, false) & !mask) | immediate
            } else {
                immediate
            };
            self.write_reg(rd, value, false, wide);
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // ADD/SUB immediate, including the SP form when S=0.
        if word & 0x1f000000 == 0x11000000 {
            let subtract = word & (1 << 30) != 0;
            let set_flags = word & (1 << 29) != 0;
            let shift = if word & (1 << 22) != 0 { 12 } else { 0 };
            let immediate = u64::from((word >> 10) & 0xfff) << shift;
            let left = self.read_reg(rn, true);
            let (value, carry, overflow) = add_sub(left, immediate, subtract, wide);
            self.write_reg(rd, value, !set_flags, wide);
            if set_flags {
                self.set_nzcv(value, wide, carry, overflow);
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // ADD/SUB extended register. Rn=31 is SP, Rm=31 is ZR.
        if word & 0x1fe00000 == 0x0b200000 {
            let subtract = word & (1 << 30) != 0;
            let set_flags = word & (1 << 29) != 0;
            let option = (word >> 13) & 7;
            let amount = (word >> 10) & 7;
            if amount > 4 {
                self.raise(GuestException {
                    kind: ExceptionKind::UndefinedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let width = if wide { 64 } else { 32 };
            let bits = (8u32 << (option & 3)).min(width);
            let raw = self.read_reg((word >> 16) & 31, false);
            let extended = if option & 4 != 0 {
                (((raw << (64 - bits)) as i64) >> (64 - bits)) as u64
            } else {
                raw & (u64::MAX >> (64 - bits))
            };
            let right = extended << amount;
            let left = self.read_reg(rn, true);
            let (value, carry, overflow) = add_sub(left, right, subtract, wide);
            self.write_reg(rd, value, !set_flags, wide);
            if set_flags {
                self.set_nzcv(value, wide, carry, overflow);
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        // ADD/SUB shifted register, LSL/LSR/ASR at the operand width.
        if word & 0x1f200000 == 0x0b000000 {
            let subtract = word & (1 << 30) != 0;
            let set_flags = word & (1 << 29) != 0;
            let shift_type = (word >> 22) & 3;
            let amount = (word >> 10) & 0x3f;
            if shift_type == 3 || (!wide && amount >= 32) {
                self.raise(GuestException {
                    kind: ExceptionKind::UndefinedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let mut right=self.read_reg((word >> 16) & 31, false);
            if !wide {right&=0xffff_ffff;}
            right=match shift_type {
                0=>right<<amount,
                1=>right>>amount,
                _=>if wide {((right as i64)>>amount) as u64}
                    else {(((right as u32 as i32)>>amount) as u32) as u64},
            };
            let left = self.read_reg(rn, false);
            let (value, carry, overflow) = add_sub(left, right, subtract, wide);
            self.write_reg(rd, value, false, wide);
            if set_flags {
                self.set_nzcv(value, wide, carry, overflow);
            }
            self.pc = pc.wrapping_add(4);
            return StepResult::Continue;
        }

        if word & 0x3a000000 == 0x28000000 {
            return match self.pair_memory(bus, word) {
                Ok(()) => StepResult::Continue,
                Err((kind, far)) => {
                    let mut syndrome = match kind {
                        ExceptionKind::DataAbort | ExceptionKind::AlignmentFault => {
                            let fsc = if kind == ExceptionKind::AlignmentFault { ESR_FSC_ALIGNMENT }
                                else { ESR_FSC_TRANSLATION_L3 };
                            (expected_ec(kind, self.current_el).unwrap() << 26) | (1 << 25) | fsc |
                                if word & (1 << 22) == 0 { ESR_ISS_WNR } else { 0 }
                        }
                        _ => word as u64,
                    };
                    if kind == ExceptionKind::SpAlignmentFault { syndrome = (0x26 << 26) | (1 << 25); }
                    self.raise(GuestException { kind, instruction: word, syndrome, far, pc });
                    StepResult::Exception(kind)
                }
            };
        }

        // Integer scaled/unscaled immediate and register-offset scalar transfers.
        if word & 0x3b000000 == 0x39000000 || word & 0x3b200c00 == 0x38200800 ||
            word & 0x3b200c00 == 0x38000000 || word & 0x3b200400 == 0x38000400 {
            return match self.scalar_memory(bus, word) {
                Ok(()) => StepResult::Continue,
                Err((kind, far)) => {
                    let syndrome = match kind {
                        ExceptionKind::DataAbort | ExceptionKind::TranslationFault |
                        ExceptionKind::PermissionFault | ExceptionKind::AlignmentFault => {
                            let fsc = match kind {
                                ExceptionKind::PermissionFault => ESR_FSC_PERMISSION_L3,
                                ExceptionKind::AlignmentFault => ESR_FSC_ALIGNMENT,
                                _ => ESR_FSC_TRANSLATION_L3,
                            };
                            (expected_ec(kind, self.current_el).unwrap() << 26) | (1 << 25) | fsc |
                                if word & (3 << 22) == 0 {ESR_ISS_WNR} else {0}
                        }
                        ExceptionKind::SpAlignmentFault => (0x26 << 26) | (1 << 25),
                        _ => u64::from(word),
                    };
                    self.raise(GuestException {kind, instruction:word, syndrome, far, pc});
                    StepResult::Exception(kind)
                }
            };
        }

        if word & 0xfc000000 == 0x14000000 {
            let offset = sign_extend(u64::from(word & 0x03ff_ffff), 26) << 2;
            self.pc = pc.wrapping_add(offset as u64);
            return StepResult::Continue;
        }

        // Unconditional branch (register): BR, BLR, RET.
        let branch_register = word & 0xffff_fc1f;
        if matches!(branch_register, 0xd61f_0000 | 0xd63f_0000 | 0xd65f_0000) {
            // Match the native profile's Rn31 rejection. Architecturally XZR
            // is the source here, never SP; this is a supported-profile limit.
            if rn == 31 {
                self.raise(GuestException {
                    kind: ExceptionKind::UndefinedInstruction,
                    instruction: word,
                    syndrome: word as u64,
                    far: pc,
                    pc,
                });
                return StepResult::Exception(ExceptionKind::UndefinedInstruction);
            }
            let target = self.read_reg(rn, false);
            // Capture the target before BLR writes X30, including BLR X30.
            if branch_register == 0xd63f_0000 {
                self.x[30] = pc.wrapping_add(4);
            }
            self.pc = target;
            return StepResult::Continue;
        }

        if word & 0x7e000000 == 0x36000000 {
            let bit = ((word >> 26) & 32) | ((word >> 19) & 31);
            let selected = (self.read_reg(rd, false) >> bit) & 1;
            let take = selected == ((word >> 24) & 1) as u64;
            let offset = sign_extend(u64::from((word >> 5) & 0x3fff), 14) * 4;
            self.pc = pc.wrapping_add(if take {offset as u64} else {4});
            return StepResult::Continue;
        }

        if word & 0x7e000000 == 0x34000000 {
            let value = self.read_reg(rd, false);
            let value = if wide { value } else { u64::from(value as u32) };
            let nonzero = word & (1 << 24) != 0;
            let offset = sign_extend(u64::from((word >> 5) & 0x7ffff), 19) << 2;
            let take = if nonzero { value != 0 } else { value == 0 };
            self.pc = if take {
                pc.wrapping_add(offset as u64)
            } else {
                pc.wrapping_add(4)
            };
            return StepResult::Continue;
        }

        self.raise(GuestException {
            kind: ExceptionKind::UndefinedInstruction,
            instruction: word,
            syndrome: word as u64,
            far: pc,
            pc,
        });
        StepResult::Exception(ExceptionKind::UndefinedInstruction)
    }

    /// Execute code from a caller-owned buffer with a hard architectural
    /// instruction budget. Code is copied into guest RAM so that instruction
    /// fetches, page walks, and data accesses all use the same guest address
    /// space; the caller's original code buffer remains read-only.
    pub(crate) fn run_bounded(
        &mut self,
        code: &[u8],
        ram: &mut [u8],
        budget: u64,
    ) -> ArchRunResult {
        self.run_bounded_with_hook(code, ram, budget, |_| {})
    }

    /// Execute a bounded guest while notifying the enclosing machine after
    /// each committed instruction.  The hook observes architectural state
    /// only after the instruction and counter update, so a device graph can
    /// mirror timer/IRQ state without participating in decode or host-code
    /// emission.  It is intentionally synchronous and allocation-free.
    pub(crate) fn run_bounded_with_hook<F>(
        &mut self,
        code: &[u8],
        ram: &mut [u8],
        budget: u64,
        mut after_step: F,
    ) -> ArchRunResult
    where
        F: FnMut(&Self),
    {
        let mut bus = RamBus::new(ram);
        self.run_bounded_with_bus(code, &mut bus, budget, |state| after_step(state))
    }

    /// Execute through a machine-owned bus.  The decoder and architectural
    /// state are shared with the RAM-only reference path; only address-space
    /// ownership changes.  This is the integration seam for the native M1
    /// graph and later device implementations.
    pub(crate) fn run_bounded_with_bus<B, F>(
        &mut self,
        code: &[u8],
        bus: &mut B,
        budget: u64,
        after_step: F,
    ) -> ArchRunResult
    where
        B: GuestBus,
        F: FnMut(&Self),
    {
        if !self.state_valid()
            || code.len() < 4
            || code.len() & 3 != 0
            || budget == 0
            || !bus.load_code(code)
        {
            return ArchRunResult {
                status: ArchRunStatus::Input,
                exception: None,
                retired: self.retired,
                pc: self.pc,
            };
        }
        // `retired` is the consumption for this bounded invocation, not a
        // lifetime counter.  A caller may reuse the architectural state for
        // another bounded guest after a halt or exception; carrying the old
        // count into the new budget would skip execution or report a stale
        // result.
        self.retired = 0;
        self.pc = 0;
        self.pending_exception = None;
        self.exception_target = None;
        self.exception_from_lower_el = false;
        self.exception_vector = 0;
        self.waiting = false;
        self.run_loaded_with_bus(bus, budget, after_step)
    }

    /// Enter an already loaded physical image on the x86 EFI execution path.
    /// The RAM slice is guest backing, never a host-address identity mapping.
    pub(crate) fn run_boot_bounded(
        &mut self, ram: &mut [u8], ram_base: u64, entry: u64,
        args: u64, stack: u64, budget: u64,
    ) -> ArchRunResult {
        let end = ram_base.checked_add(ram.len() as u64);
        if budget == 0 || ram_base & 0x3fff != 0 || entry & 3 != 0
            || args & 7 != 0 || stack & 15 != 0
            || end.is_none_or(|end| entry < ram_base || entry.checked_add(4).is_none_or(|v| v > end)
                || args < ram_base || args >= end || stack <= ram_base || stack > end)
        {
            return ArchRunResult { status: ArchRunStatus::Input, exception: None,
                retired: 0, pc: self.pc };
        }
        *self = Self::reset(self.affinity);
        self.pc = entry;
        self.x[0] = args;
        self.sp = stack;
        self.sp_el[1] = stack;
        self.pstate |= PSTATE_D | PSTATE_A | PSTATE_I | PSTATE_F;
        let mut bus = RamBus { ram, base: ram_base };
        self.run_loaded_with_bus(&mut bus, budget, |_| {})
    }

    fn run_loaded_with_bus<B: GuestBus, F: FnMut(&Self)>(
        &mut self, bus: &mut B, budget: u64, mut after_step: F,
    ) -> ArchRunResult {
        while self.retired < budget {
            if self.poll_interrupt() {
                let pending = self.pending_exception;
                let exception = self.commit_pending_interrupt().or(pending);
                return ArchRunResult {
                    status: ArchRunStatus::Exception,
                    exception,
                    retired: self.retired,
                    pc: self.pc,
                };
            }
            let result = self.execute_one(bus);
            match result {
                StepResult::Continue => {
                    self.retired = self.retired.saturating_add(1);
                    self.advance_counter(1);
                    bus.after_instruction(self);
                    after_step(self);
                }
                StepResult::Halt => {
                    self.retired = self.retired.saturating_add(1);
                    self.advance_counter(1);
                    bus.after_instruction(self);
                    after_step(self);
                    return ArchRunResult {
                        status: ArchRunStatus::Halt,
                        exception: None,
                        retired: self.retired,
                        pc: self.pc,
                    };
                }
                StepResult::Wait => {
                    self.retired = self.retired.saturating_add(1);
                    self.advance_counter(1);
                    bus.after_instruction(self);
                    after_step(self);
                    return ArchRunResult {
                        status: ArchRunStatus::Wait,
                        exception: None,
                        retired: self.retired,
                        pc: self.pc,
                    };
                }
                StepResult::Exception(kind) => {
                    return ArchRunResult {
                        status: ArchRunStatus::Exception,
                        exception: self.pending_exception.or(Some(GuestException {
                            kind,
                            instruction: 0,
                            syndrome: 0,
                            far: self.pc,
                            pc: self.pc,
                        })),
                        retired: self.retired,
                        pc: self.pc,
                    };
                }
            }
        }
        ArchRunResult {
            status: ArchRunStatus::Budget,
            exception: None,
            retired: self.retired,
            pc: self.pc,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum StepResult {
    Continue,
    Halt,
    Wait,
    Exception(ExceptionKind),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub(crate) enum ArchRunStatus {
    Halt = 1,
    Budget = 2,
    Exception = 3,
    Wait = 4,
    Input = 5,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct ArchRunResult {
    pub(crate) status: ArchRunStatus,
    pub(crate) exception: Option<GuestException>,
    pub(crate) retired: u64,
    pub(crate) pc: u64,
}

fn map_mmu_fault(fault: MmuFault) -> ExceptionKind {
    match fault {
        MmuFault::AddressSize | MmuFault::Translation | MmuFault::AccessFlag => {
            ExceptionKind::TranslationFault
        }
        MmuFault::Permission => ExceptionKind::PermissionFault,
        MmuFault::Alignment => ExceptionKind::AlignmentFault,
    }
}

fn add_sub(left: u64, right: u64, subtract: bool, wide: bool) -> (u64, bool, bool) {
    let mask = if wide { u64::MAX } else { u64::from(u32::MAX) };
    let left = left & mask;
    let right = right & mask;
    if subtract {
        let value = left.wrapping_sub(right) & mask;
        let carry = left >= right;
        let overflow =
            ((left ^ right) & (left ^ value) & (1u64 << if wide { 63 } else { 31 })) != 0;
        (value, carry, overflow)
    } else {
        let wide_sum = (left as u128) + (right as u128);
        let value = (wide_sum as u64) & mask;
        let carry = (wide_sum >> if wide { 64 } else { 32 }) != 0;
        let sign = 1u64 << if wide { 63 } else { 31 };
        let overflow = (!(left ^ right) & (left ^ value) & sign) != 0;
        (value, carry, overflow)
    }
}

fn sign_extend(value: u64, bits: u32) -> i64 {
    let shift = 64 - bits;
    ((value << shift) as i64) >> shift
}

fn read_u32(memory: &[u8], address: u64) -> Option<u32> {
    let index = usize::try_from(address).ok()?;
    let bytes = memory.get(index..index.checked_add(4)?)?;
    Some(u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
}

fn read_u64(memory: &[u8], address: u64) -> Option<u64> {
    let index = usize::try_from(address).ok()?;
    let bytes = memory.get(index..index.checked_add(8)?)?;
    Some(u64::from_le_bytes([
        bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
    ]))
}

fn read_width(memory: &[u8], index: usize, width: usize) -> Option<u64> {
    let bytes = memory.get(index..index.checked_add(width)?)?;
    let mut value = 0u64;
    for (shift, byte) in bytes.iter().enumerate() {
        value |= u64::from(*byte) << (shift * 8);
    }
    Some(value)
}

fn write_width(memory: &mut [u8], index: usize, width: usize, value: u64) -> bool {
    let Some(bytes) = memory.get_mut(index..index.saturating_add(width)) else {
        return false;
    };
    for (shift, byte) in bytes.iter_mut().enumerate() {
        *byte = (value >> (shift * 8)) as u8;
    }
    true
}


#[test]fn matrix_reference_ids(){for word in [0xd5380620u32,0xd5380700]{let mut cpu=GuestCpuState::reset(0);cpu.x[0]=0xfeed;cpu.sp=0x800;cpu.pstate=0xf00003c5;let mut ram=[0u8;8];ram[..4].copy_from_slice(&word.to_le_bytes());let before=ram;let result=cpu.execute_one(&mut RamBus{ram:&mut ram,base:0});println!("reference word={:x} result={:?} x0={:x} pc={} sp={:x} pstate={:x} ram_equal={}",word,result,cpu.x[0],cpu.pc,cpu.sp,cpu.pstate,ram==before);}}
#[test]fn matrix_reference_mmu_controls(){for kind in 0..11{let mut mmu=crate::mmu::VfMmu::disabled();let mut tcr=16|(16<<16)|(2<<30)|(5u64<<32);let mut ttbr=0x10000000;let mut asid=0;match kind{1=>tcr=17|(17<<16)|(2<<14)|(1<<30)|(5u64<<32),2=>tcr=(tcr&!((3<<14)|(3<<30)))|(1<<14)|(3<<30),3=>{ttbr|=1<<48;asid=0xabcd;},4=>{tcr|=1<<36;asid=0xabcd;},5..=10=>tcr=(tcr&!(7<<32))|(((kind-5)as u64)<<32),_=>{}}println!("reference_control_kind={} accepted={}",kind,mmu.configure_tcr(ttbr,ttbr,tcr,asid));}}
#[test]fn matrix_reference_endian(){for big in [false,true]{let mut cpu=GuestCpuState::reset(0);if big{cpu.sys.sctlr_el1|=1<<25;}cpu.x[1]=16;let mut ram=[0u8;32];ram[..4].copy_from_slice(&0xb9400020u32.to_le_bytes());ram[16..20].copy_from_slice(&[0x11,0x22,0x33,0x44]);let result=cpu.execute_one(&mut RamBus{ram:&mut ram,base:0});println!("reference_EE={} result={:?} value={:x}",big,result,cpu.x[0]);}}

#[test]fn matrix_reference_output_width(){for ips in [2u64,5]{for bits in [39,40,47,48]{let mut mmu=crate::mmu::VfMmu::disabled();assert!(mmu.configure_tcr(0x1000,0,16|(ips<<32),0));let entries=[(0x1000,0x2003),(0x2000,0x3003),(0x3000,0x4003),(0x4000,(1u64<<bits)|0x403)];let result=mmu.translate(0,crate::mmu::Access::Read,ExceptionLevel::El1,|address|entries.iter().find(|(a,_)|*a==address).map(|(_,v)|*v));println!("reference_IPS={} PA_bit={} result={:?}",ips,bits,result);}}}
