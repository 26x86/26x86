//! Fixed-storage native-machine descriptors used by the Phase-1 preOS.
//!
//! This is deliberately a descriptor layer, not a hidden VM framework.  It
//! owns no firmware pointers, does not allocate, and has no device callbacks.
//! A future device may be attached only after its guest-visible contract has
//! been validated by the caller.  Keeping the registry here means adding a
//! device does not require changing the EFI entry or the C JIT ABI.

#![allow(dead_code)]

use super::{
    VfPreosContext, FIXED_GUEST_RAM_BYTES, MACHINE_PROFILE_M1_DIAGNOSTIC, MAX_EXECUTION_BUDGET,
    TERMINATION_HALT, TERMINATION_INTERNAL, TERMINATION_NONE,
};

pub(crate) const MAX_RAM_REGIONS: usize = 4;
pub(crate) const MAX_MMIO_REGIONS: usize = 8;
pub(crate) const MMIO_KIND_DIAGNOSTIC: u32 = 1;
pub(crate) const MMIO_WIDTH_1: u32 = 1 << 0;
pub(crate) const MMIO_WIDTH_2: u32 = 1 << 1;
pub(crate) const MMIO_WIDTH_4: u32 = 1 << 2;
pub(crate) const MMIO_WIDTH_8: u32 = 1 << 3;
const MMIO_WIDTHS_ALL: u32 = MMIO_WIDTH_1 | MMIO_WIDTH_2 | MMIO_WIDTH_4 | MMIO_WIDTH_8;

#[derive(Clone, Copy)]
pub(crate) struct VfCpuContext {
    pub(crate) x: [u64; 31],
    pub(crate) sp: u64,
    pub(crate) retired_instruction_count: u64,
    pub(crate) guest_pc: u64,
    pub(crate) pstate: u64,
    pub(crate) current_el: u8,
    pub(crate) exception_pending: u32,
    pub(crate) sctlr: u64,
    pub(crate) ttbr0: u64,
    pub(crate) ttbr1: u64,
    pub(crate) tcr: u64,
    pub(crate) mair: u64,
    pub(crate) vbar: u64,
    pub(crate) esr: u64,
    pub(crate) far: u64,
    pub(crate) elr: u64,
    pub(crate) cntfrq: u64,
    pub(crate) cntpct: u64,
    pub(crate) cntp_ctl: u64,
    pub(crate) cntp_cval: u64,
    pub(crate) smp_affinity: u32,
}

#[derive(Clone, Copy)]
pub(crate) struct VfRamRegion {
    pub(crate) base: u64,
    pub(crate) bytes: u64,
}

impl VfRamRegion {
    fn empty() -> Self {
        Self { base: 0, bytes: 0 }
    }

    fn end(self) -> Option<u64> {
        self.base.checked_add(self.bytes)
    }

    fn contains(self, address: u64, bytes: u64) -> bool {
        match (self.end(), address.checked_add(bytes)) {
            (Some(end), Some(access_end)) => {
                self.bytes != 0 && address >= self.base && access_end <= end
            }
            _ => false,
        }
    }
}

#[derive(Clone, Copy)]
pub(crate) struct VfMmioRegion {
    pub(crate) base: u64,
    pub(crate) bytes: u64,
    pub(crate) kind: u32,
    pub(crate) access_widths: u32,
    pub(crate) read_only: bool,
}

impl VfMmioRegion {
    const EMPTY: Self = Self {
        base: 0,
        bytes: 0,
        kind: 0,
        access_widths: 0,
        read_only: false,
    };

    fn end(self) -> Option<u64> {
        self.base.checked_add(self.bytes)
    }

    fn contains(self, address: u64, bytes: u64) -> bool {
        match (self.end(), address.checked_add(bytes)) {
            (Some(end), Some(access_end)) => {
                self.bytes != 0 && address >= self.base && access_end <= end
            }
            _ => false,
        }
    }
}

pub(crate) struct VfGuestPhysicalAddressSpace {
    pub(crate) ram_regions: [VfRamRegion; MAX_RAM_REGIONS],
    pub(crate) ram_count: u32,
}

impl VfGuestPhysicalAddressSpace {
    fn empty() -> Self {
        Self {
            ram_regions: [VfRamRegion::empty(); MAX_RAM_REGIONS],
            ram_count: 0,
        }
    }

    fn add_ram(&mut self, region: VfRamRegion) -> bool {
        if region.bytes == 0 || region.base & 0xfff != 0 || region.bytes & 0xfff != 0 {
            return false;
        }
        if self.ram_count as usize >= MAX_RAM_REGIONS || region.end().is_none() {
            return false;
        }
        if self.overlaps(region.base, region.bytes) {
            return false;
        }
        self.ram_regions[self.ram_count as usize] = region;
        self.ram_count += 1;
        true
    }

    fn overlaps(&self, base: u64, bytes: u64) -> bool {
        self.ram_regions[..self.ram_count as usize]
            .iter()
            .any(|existing| ranges_overlap(existing.base, existing.bytes, base, bytes))
    }

    fn contains(&self, address: u64, bytes: u64) -> bool {
        self.ram_regions[..self.ram_count as usize]
            .iter()
            .any(|region| region.contains(address, bytes))
    }
}

pub(crate) struct VfMmioRegistry {
    pub(crate) regions: [VfMmioRegion; MAX_MMIO_REGIONS],
    pub(crate) region_count: u32,
}

impl VfMmioRegistry {
    fn empty() -> Self {
        Self {
            regions: [VfMmioRegion::EMPTY; MAX_MMIO_REGIONS],
            region_count: 0,
        }
    }

    /// Register a fixed, page-aligned guest-visible MMIO window.
    ///
    /// This only records the window and access policy.  It intentionally does
    /// not manufacture register values or IRQ behaviour for an unproven
    /// device.  A caller that has no device contract leaves the registry
    /// empty; a synthetic diagnostic device can use `MMIO_KIND_DIAGNOSTIC`.
    pub(crate) fn register(
        &mut self,
        region: VfMmioRegion,
        gpa: &VfGuestPhysicalAddressSpace,
    ) -> bool {
        if region.kind == 0
            || region.bytes == 0
            || region.base & 0xfff != 0
            || region.bytes & 0xfff != 0
            || region.access_widths == 0
            || region.access_widths & !MMIO_WIDTHS_ALL != 0
            || region.end().is_none()
            || self.region_count as usize >= MAX_MMIO_REGIONS
            || gpa.overlaps(region.base, region.bytes)
        {
            return false;
        }
        if self.regions[..self.region_count as usize]
            .iter()
            .any(|existing| {
                ranges_overlap(existing.base, existing.bytes, region.base, region.bytes)
            })
        {
            return false;
        }
        self.regions[self.region_count as usize] = region;
        self.region_count += 1;
        true
    }

    pub(crate) fn lookup(&self, address: u64, bytes: u64, write: bool) -> Option<VfMmioRegion> {
        let width_bit = match bytes {
            1 => MMIO_WIDTH_1,
            2 => MMIO_WIDTH_2,
            4 => MMIO_WIDTH_4,
            8 => MMIO_WIDTH_8,
            _ => 0,
        };
        if width_bit == 0 || address & (bytes - 1) != 0 {
            return None;
        }
        self.regions[..self.region_count as usize]
            .iter()
            .copied()
            .find(|region| {
                region.contains(address, bytes)
                    && region.access_widths & width_bit != 0
                    && !(write && region.read_only)
            })
    }
}

pub(crate) struct VfExecutionBudget {
    pub(crate) limit: u64,
    pub(crate) consumed: u64,
}

pub(crate) struct VfTerminationReason {
    pub(crate) value: u32,
}

pub(crate) struct VfMachineProfile {
    pub(crate) value: u32,
}

pub(crate) struct VfMachine {
    pub(crate) cpu: VfCpuContext,
    /// Canonical guest architectural state. `cpu` remains the C-JIT result
    /// mirror; this object owns EL/system/MMU/timer/SMP state for the Rust
    /// reference path and is never an EFI context.
    pub(crate) arch: crate::arch::GuestCpuState,
    pub(crate) mmu: crate::mmu::VfMmu,
    pub(crate) guest_physical_address_space: VfGuestPhysicalAddressSpace,
    pub(crate) mmio: VfMmioRegistry,
    // VMApple is a bounded guest-visible graph descriptor.  It is kept
    // separate from the Phase-1 diagnostic address space and is never
    // substituted for the native M1 AIC/DART contract.
    pub(crate) vmapple: Option<crate::vmapple::VfVmappleMachine>,
    // Native M1-only graph.  This is distinct from the portable VMApple
    // descriptor and owns the DART/DMA, recovery, display, timer/AIC, and
    // firmware-handoff contract primitives.
    pub(crate) m1: crate::m1::M1MachineGraph,
    pub(crate) execution_budget: VfExecutionBudget,
    pub(crate) termination_reason: VfTerminationReason,
    pub(crate) profile: VfMachineProfile,
    pub(crate) reset_generation: u32,
}

impl VfMachine {
    pub(crate) fn seed(context: &VfPreosContext) -> Self {
        let mut machine = Self {
            cpu: VfCpuContext {
                x: [0; 31],
                sp: 0,
                retired_instruction_count: 0,
                guest_pc: 0,
                pstate: 0,
                current_el: 1,
                exception_pending: 0,
                sctlr: 0,
                ttbr0: 0,
                ttbr1: 0,
                // TCR_EL1 reset value used by the reference 4 KiB TTBR0
                // configuration.  The C-JIT mirror is kept in step with the
                // canonical GuestCpuState bank.
                tcr: 16,
                mair: 0,
                vbar: 0,
                esr: 0,
                far: 0,
                elr: 0,
                cntfrq: 24_000_000,
                cntpct: 0,
                cntp_ctl: 0,
                cntp_cval: 0,
                smp_affinity: 0,
            },
            arch: crate::arch::GuestCpuState::reset(0),
            mmu: crate::mmu::VfMmu::disabled(),
            guest_physical_address_space: VfGuestPhysicalAddressSpace::empty(),
            mmio: VfMmioRegistry::empty(),
            vmapple: crate::vmapple::VfVmappleMachine::new(1, context.guest_ram_size, 0),
            m1: crate::m1::M1MachineGraph::new(context.guest_ram_size),
            execution_budget: VfExecutionBudget {
                limit: context.execution_budget,
                consumed: 0,
            },
            termination_reason: VfTerminationReason {
                value: TERMINATION_NONE,
            },
            profile: VfMachineProfile {
                value: context.machine_profile,
            },
            reset_generation: 0,
        };
        let _ = machine.guest_physical_address_space.add_ram(VfRamRegion {
            base: 0,
            bytes: context.guest_ram_size,
        });
        machine
    }

    /// Reset CPU-visible execution state while preserving the validated
    /// machine topology.  The generation is monotonic and is evidence that a
    /// reset hook was actually called; it is not a firmware reset operation.
    pub(crate) fn reset(&mut self) {
        self.cpu = VfCpuContext {
            x: [0; 31],
            sp: 0,
            retired_instruction_count: 0,
            guest_pc: 0,
            pstate: 0,
            current_el: 1,
            exception_pending: 0,
            sctlr: 0,
            ttbr0: 0,
            ttbr1: 0,
            tcr: 16,
            mair: 0,
            vbar: 0,
            esr: 0,
            far: 0,
            elr: 0,
            cntfrq: 24_000_000,
            cntpct: 0,
            cntp_ctl: 0,
            cntp_cval: 0,
            smp_affinity: 0,
        };
        self.arch = crate::arch::GuestCpuState::reset(0);
        self.mmu.invalidate();
        self.execution_budget.limit = self.execution_budget.limit.min(MAX_EXECUTION_BUDGET);
        self.execution_budget.consumed = 0;
        self.termination_reason.value = TERMINATION_NONE;
        if let Some(vmapple) = self.vmapple.as_mut() {
            vmapple.reset();
        }
        self.m1.reset();
        self.reset_generation = self.reset_generation.saturating_add(1);
    }

    pub(crate) fn register_synthetic_diagnostic_mmio(&mut self) -> bool {
        self.mmio.register(
            VfMmioRegion {
                base: 0x1000_0000,
                bytes: 0x1000,
                kind: MMIO_KIND_DIAGNOSTIC,
                access_widths: MMIO_WIDTH_4,
                read_only: true,
            },
            &self.guest_physical_address_space,
        )
    }

    pub(crate) fn valid_seed(&self) -> bool {
        self.profile.value == MACHINE_PROFILE_M1_DIAGNOSTIC
            && self.reset_generation != 0
            && self.guest_physical_address_space.ram_count == 1
            && self.guest_physical_address_space.ram_regions[0].base == 0
            && self.guest_physical_address_space.ram_regions[0].bytes == FIXED_GUEST_RAM_BYTES
            && (self.mmio.region_count as usize) <= MAX_MMIO_REGIONS
            && self.execution_budget.limit != 0
            && self.execution_budget.consumed == 0
            && self.execution_budget.limit <= MAX_EXECUTION_BUDGET
            && self.arch.state_valid()
            && self.arch.current_el == crate::arch::ExceptionLevel::El1
            && self.arch.affinity == 0
            && self.arch.sys.cntfrq_el0 == 24_000_000
            && self
                .vmapple
                .as_ref()
                .map_or(false, crate::vmapple::VfVmappleMachine::valid)
            && self.m1.valid()
    }

    pub(crate) fn vmapple_graph_ready(&self) -> bool {
        self.vmapple
            .as_ref()
            .map_or(false, crate::vmapple::VfVmappleMachine::valid)
    }

    pub(crate) fn m1_graph_ready(&self) -> bool {
        self.m1.valid()
    }

    pub(crate) fn architecture_ready(&self) -> bool {
        self.arch.state_valid()
            && self.arch.current_el == crate::arch::ExceptionLevel::El1
            && self.arch.affinity == 0
            && self.arch.smp.cpu_count == 1
            && self.arch.smp.online_mask & 1 != 0
            && self.arch.sys.cntfrq_el0 == 24_000_000
            && !self.arch.mmu.enabled
            && self.arch.pending_exception.is_none()
    }

    pub(crate) fn valid_topology(&self) -> bool {
        if self.guest_physical_address_space.ram_count as usize > MAX_RAM_REGIONS
            || self.mmio.region_count as usize > MAX_MMIO_REGIONS
        {
            return false;
        }
        for region in self.mmio.regions[..self.mmio.region_count as usize].iter() {
            if region.kind == 0
                || region.access_widths == 0
                || region.access_widths & !MMIO_WIDTHS_ALL != 0
                || region.end().is_none()
                || self
                    .guest_physical_address_space
                    .overlaps(region.base, region.bytes)
            {
                return false;
            }
        }
        true
    }

    /// Accept the bounded result only after checking the machine-owned
    /// execution contract.  The C JIT already enforces the same budget, but
    /// this second check prevents a malformed or future wrapper from turning
    /// an over-budget result into a successful Rust normalization.
    pub(crate) fn accept_execution_result(
        &mut self,
        retired: u64,
        guest_pc: u64,
        termination_reason: u32,
        guest_size: u64,
        result_x0: u64,
        result_x1: u64,
        result_x3: u64,
    ) -> bool {
        if retired > self.execution_budget.limit
            || (termination_reason == TERMINATION_HALT
                && (guest_pc & 3 != 0 || guest_pc > guest_size))
        {
            self.termination_reason.value = TERMINATION_INTERNAL;
            return false;
        }
        self.cpu.retired_instruction_count = retired;
        self.cpu.guest_pc = guest_pc;
        self.cpu.x[0] = result_x0;
        self.cpu.x[1] = result_x1;
        self.cpu.x[3] = result_x3;
        self.arch.retired = retired;
        self.arch.pc = guest_pc;
        self.arch.x[0] = result_x0;
        self.arch.x[1] = result_x1;
        self.arch.x[3] = result_x3;
        self.execution_budget.consumed = retired;
        self.termination_reason.value = termination_reason;
        true
    }

    #[cfg(test)]
    pub(crate) fn ram_contains(&self, address: u64, bytes: u64) -> bool {
        self.guest_physical_address_space.contains(address, bytes)
    }
}

fn ranges_overlap(left_base: u64, left_bytes: u64, right_base: u64, right_bytes: u64) -> bool {
    match (
        left_base.checked_add(left_bytes),
        right_base.checked_add(right_bytes),
    ) {
        (Some(left_end), Some(right_end)) => left_base < right_end && right_base < left_end,
        _ => true,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use core::ffi::c_void;
    use core::mem::size_of;

    unsafe extern "C" fn trace(_: *const u8, _: *mut c_void) {}

    fn context() -> VfPreosContext {
        VfPreosContext {
            abi_version: 1,
            struct_size: size_of::<VfPreosContext>() as u32,
            machine_profile: MACHINE_PROFILE_M1_DIAGNOSTIC,
            flags: 0,
            execution_budget: 100,
            guest_bytes: 0x1000 as *const u8,
            guest_size: 4,
            guest_ram: 0x2000 as *mut u8,
            guest_ram_size: FIXED_GUEST_RAM_BYTES,
            opaque_execution_handle: 0x3000 as *mut c_void,
            trace: Some(trace),
            trace_opaque: core::ptr::null_mut(),
            expected_x1: 0,
            expected_x3: 0,
            expected_ram_offset: 0,
            expected_ram_qword: 0,
            expected_retired: 0,
            expected_guest_pc: 0,
            reserved: [0; 3],
        }
    }

    #[test]
    fn seed_reset_and_topology_are_explicit() {
        let mut machine = VfMachine::seed(&context());
        assert!(!machine.valid_seed());
        machine.reset();
        assert!(machine.valid_seed());
        assert!(machine.valid_topology());
        assert!(machine.vmapple_graph_ready());
        assert!(machine.m1_graph_ready());
        assert_eq!(machine.m1.identity.soc_id, crate::m1::M1_SOC_T8103);
        assert_eq!(machine.m1.identity.cpu_count, crate::m1::M1_CPU_COUNT);
        assert_eq!(
            machine.vmapple.as_ref().map(|graph| graph.cpu_count),
            Some(1)
        );
        assert!(machine.ram_contains(0, 8));
        assert!(!machine.ram_contains(FIXED_GUEST_RAM_BYTES, 1));
    }

    #[test]
    fn static_mmio_registry_rejects_overlap_and_proves_permissions() {
        let mut machine = VfMachine::seed(&context());
        machine.reset();
        assert!(machine.register_synthetic_diagnostic_mmio());
        assert!(machine.valid_seed());
        assert!(machine.valid_topology());
        assert_eq!(machine.mmio.region_count, 1);
        assert!(machine.mmio.lookup(0x1000_0000, 4, false).is_some());
        assert!(machine.mmio.lookup(0x1000_0000, 2, false).is_none());
        assert!(machine.mmio.lookup(0x1000_0002, 4, false).is_none());
        assert!(machine.mmio.lookup(0x1000_0000, 4, true).is_none());
        assert!(!machine.mmio.register(
            VfMmioRegion {
                base: 0x1000_0000,
                bytes: 0x1000,
                kind: MMIO_KIND_DIAGNOSTIC,
                access_widths: MMIO_WIDTH_4,
                read_only: true,
            },
            &machine.guest_physical_address_space,
        ));
        assert!(!machine.mmio.register(
            VfMmioRegion {
                base: 0,
                bytes: 0x1000,
                kind: MMIO_KIND_DIAGNOSTIC,
                access_widths: MMIO_WIDTH_4,
                read_only: false,
            },
            &machine.guest_physical_address_space,
        ));
        assert!(!machine.mmio.register(
            VfMmioRegion {
                base: 0x2000_0000,
                bytes: 0x1000,
                kind: MMIO_KIND_DIAGNOSTIC,
                access_widths: 1 << 7,
                read_only: true,
            },
            &machine.guest_physical_address_space,
        ));
    }

    #[test]
    fn reset_preserves_topology_and_clears_execution_state() {
        let mut machine = VfMachine::seed(&context());
        machine.reset();
        assert!(machine.register_synthetic_diagnostic_mmio());
        machine.cpu.retired_instruction_count = 17;
        machine.cpu.guest_pc = 12;
        machine.termination_reason.value = 3;
        let generation = machine.reset_generation;
        let vmapple_generation = machine
            .vmapple
            .as_ref()
            .map(|graph| graph.reset_generation)
            .unwrap();
        let m1_generation = machine.m1.reset_generation;
        machine.reset();
        assert_eq!(machine.cpu.retired_instruction_count, 0);
        assert_eq!(machine.cpu.guest_pc, 0);
        assert_eq!(machine.termination_reason.value, TERMINATION_NONE);
        assert_eq!(machine.mmio.region_count, 1);
        assert!(machine
            .vmapple
            .as_ref()
            .map(|graph| graph.reset_generation > vmapple_generation)
            .unwrap_or(false));
        assert!(machine.m1.reset_generation > m1_generation);
        assert!(machine.reset_generation > generation);
    }

    #[test]
    fn execution_result_is_bounded_and_aligned() {
        let mut machine = VfMachine::seed(&context());
        machine.reset();
        assert!(machine.accept_execution_result(35, 32, TERMINATION_HALT, 32, 0, 55, 55));
        assert_eq!(machine.cpu.retired_instruction_count, 35);
        assert_eq!(machine.execution_budget.consumed, 35);
        assert_eq!(machine.cpu.guest_pc, 32);
        assert_eq!(machine.termination_reason.value, TERMINATION_HALT);

        assert!(!machine.accept_execution_result(101, 32, TERMINATION_HALT, 32, 0, 0, 0));
        assert_eq!(machine.termination_reason.value, TERMINATION_INTERNAL);
        machine.reset();
        assert!(!machine.accept_execution_result(1, 2, TERMINATION_HALT, 32, 0, 0, 0));
        machine.reset();
        assert!(!machine.accept_execution_result(1, 36, TERMINATION_HALT, 32, 0, 0, 0));
    }
}
