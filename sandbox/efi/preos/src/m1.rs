//! M1-only native machine contract primitives.
//!
//! This module is the native-machine side of the preOS.  It is intentionally
//! not a second loader and it does not reuse the VMApple/GIC descriptor as an
//! M1 substitute.  The graph has a fixed T8103 identity and fixed-size
//! components for the contracts that the guest-facing implementation needs:
//! interrupt routing, timer, DART-style DMA translation, storage, recovery,
//! display, and firmware handoff.
//!
//! Apple register maps and the signed iBoot protocol are not public contracts
//! in this repository.  Consequently the interfaces below implement the
//! bounded semantics and ownership boundaries without inventing Apple MMIO
//! offsets or treating an opaque recovery envelope as signature validation.
//! A later source-port can attach a verified register map to these interfaces
//! without changing the EFI entry or the C ABI.

#![allow(dead_code)]

use super::arch::{ExceptionKind, GuestBus, GuestCpuState};
use super::mmu::{Access, PAGE_SIZE};

pub(crate) const M1_SOC_T8103: u32 = 0x0000_8103;
pub(crate) const M1_CPU_COUNT: u32 = 8;
pub(crate) const M1_COUNTER_FREQUENCY: u64 = 24_000_000;
pub(crate) const M1_MAX_DEVICES: usize = 8;
pub(crate) const M1_MAX_DART_MAPPINGS: usize = 16;
pub(crate) const M1_DART_GRANULE: u64 = PAGE_SIZE;
// Recovery input is chunked.  Keeping one envelope at 1 KiB keeps the
// EFI-integrated graph below the MSVC stack-probe threshold; callers can send
// a larger signed artifact as a sequence of envelopes.
pub(crate) const M1_MAX_RECOVERY_PAYLOAD: usize = 1024;
pub(crate) const M1_RECOVERY_HEADER_BYTES: usize = 20;
pub(crate) const M1_STORAGE_BLOCK_BYTES: usize = 4096;
pub(crate) const M1_MAX_DISPLAY_WIDTH: u32 = 8192;
pub(crate) const M1_MAX_DISPLAY_HEIGHT: u32 = 8192;

// These are graph-local windows only.  They are deliberately not Apple
// physical addresses and must not be used as a physical register-map claim.
pub(crate) const M1_LOGICAL_WINDOW_BYTES: u64 = 0x1000;
pub(crate) const M1_LOGICAL_FIRMWARE_BASE: u64 = 0x0000;
pub(crate) const M1_LOGICAL_AIC_BASE: u64 = 0x1000;
pub(crate) const M1_LOGICAL_TIMER_BASE: u64 = 0x2000;
pub(crate) const M1_LOGICAL_DART_BASE: u64 = 0x3000;
pub(crate) const M1_LOGICAL_STORAGE_BASE: u64 = 0x4000;
pub(crate) const M1_LOGICAL_RECOVERY_BASE: u64 = 0x5000;
pub(crate) const M1_LOGICAL_DISPLAY_BASE: u64 = 0x6000;
pub(crate) const M1_LOGICAL_UART_BASE: u64 = 0x7000;

/// Guest-visible alias used only by the Venfire native reference bus.  The
/// logical windows remain compact for descriptor/unit tests, while this alias
/// keeps them outside the fixed 64 KiB diagnostic RAM used by the EFI ABI.
/// It is not an Apple physical register address and must not be advertised as
/// one in firmware metadata.
pub(crate) const M1_GUEST_MMIO_BASE: u64 = 0x1000_0000;
pub(crate) const M1_GUEST_MMIO_BYTES: u64 = 8 * M1_LOGICAL_WINDOW_BYTES;

const TIMER_SOURCE: u8 = 0;
const STORAGE_SOURCE: u8 = 1;
const DISPLAY_SOURCE: u8 = 2;
const RECOVERY_SOURCE: u8 = 3;
const M1_INTERRUPT_SOURCES: usize = 8;

const DMA_READ: u8 = 1;
const DMA_WRITE: u8 = 1 << 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub(crate) enum M1DeviceKind {
    Firmware = 1,
    Aic = 2,
    Timer = 3,
    Dart = 4,
    Storage = 5,
    Recovery = 6,
    Display = 7,
    Uart = 8,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1MmioFault {
    Unmapped,
    OutOfRange,
    InvalidWidth,
    ReadOnly,
    InvalidRegister,
    Unsupported,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum M1LogicalWindow {
    Firmware,
    Aic,
    Timer,
    Dart,
    Storage,
    Recovery,
    Display,
    Uart,
}

fn logical_window(address: u64, width: u32) -> Result<(M1LogicalWindow, u64), M1MmioFault> {
    let bytes = u64::from(width / 8);
    if width == 0 || width % 8 != 0 || !matches!(width, 8 | 16 | 32 | 64) {
        return Err(M1MmioFault::InvalidWidth);
    }
    let end = address.checked_add(bytes).ok_or(M1MmioFault::OutOfRange)?;
    let windows = [
        (M1_LOGICAL_FIRMWARE_BASE, M1LogicalWindow::Firmware),
        (M1_LOGICAL_AIC_BASE, M1LogicalWindow::Aic),
        (M1_LOGICAL_TIMER_BASE, M1LogicalWindow::Timer),
        (M1_LOGICAL_DART_BASE, M1LogicalWindow::Dart),
        (M1_LOGICAL_STORAGE_BASE, M1LogicalWindow::Storage),
        (M1_LOGICAL_RECOVERY_BASE, M1LogicalWindow::Recovery),
        (M1_LOGICAL_DISPLAY_BASE, M1LogicalWindow::Display),
        (M1_LOGICAL_UART_BASE, M1LogicalWindow::Uart),
    ];
    windows
        .iter()
        .find_map(|(base, window)| {
            if address >= *base && end <= base.saturating_add(M1_LOGICAL_WINDOW_BYTES) {
                Some((*window, address - *base))
            } else {
                None
            }
        })
        .ok_or(if address < M1_LOGICAL_FIRMWARE_BASE
            || address >= M1_LOGICAL_UART_BASE + M1_LOGICAL_WINDOW_BYTES
        {
            M1MmioFault::Unmapped
        } else {
            M1MmioFault::OutOfRange
        })
}

fn mmio_width(width: u32, expected: u32) -> Result<(), M1MmioFault> {
    (width == expected)
        .then_some(())
        .ok_or(M1MmioFault::InvalidWidth)
}

#[derive(Clone, Copy)]
struct M1DeviceDescriptor {
    kind: M1DeviceKind,
    instance: u8,
    contract_ready: bool,
    guest_visible: bool,
}

const EMPTY_DEVICE: M1DeviceDescriptor = M1DeviceDescriptor {
    kind: M1DeviceKind::Firmware,
    instance: 0,
    contract_ready: false,
    guest_visible: false,
};

/// The identity exposed by the native graph.  `board_id_len == 0` is
/// deliberate: a T8103 SoC identity is not a claim about one particular Mac
/// product board or its firmware personality.
#[derive(Clone, Copy)]
pub(crate) struct M1FirmwareIdentity {
    pub(crate) soc_id: u32,
    pub(crate) cpu_count: u32,
    pub(crate) aarch64: bool,
    pub(crate) macos_only: bool,
    pub(crate) board_id: [u8; 16],
    pub(crate) board_id_len: u8,
}

impl M1FirmwareIdentity {
    const fn t8103() -> Self {
        Self {
            soc_id: M1_SOC_T8103,
            cpu_count: M1_CPU_COUNT,
            aarch64: true,
            macos_only: true,
            board_id: [0; 16],
            board_id_len: 0,
        }
    }

    fn valid(&self) -> bool {
        self.soc_id == M1_SOC_T8103
            && self.cpu_count == M1_CPU_COUNT
            && self.aarch64
            && self.macos_only
            && self.board_id_len <= self.board_id.len() as u8
    }
}

#[derive(Clone, Copy)]
pub(crate) struct M1FirmwareHandoff {
    pub(crate) entry_pa: u64,
    pub(crate) device_tree_pa: u64,
    pub(crate) device_tree_bytes: u64,
    pub(crate) prepared: bool,
    /// This flag is never set by this module.  It is reserved for a future
    /// caller that has actually verified an Apple signature chain.
    pub(crate) signature_verified: bool,
}

impl M1FirmwareHandoff {
    const fn initial() -> Self {
        Self {
            entry_pa: 0,
            device_tree_pa: 0,
            device_tree_bytes: 0,
            prepared: false,
            signature_verified: false,
        }
    }

    fn prepare(&mut self, entry_pa: u64, device_tree_pa: u64, device_tree_bytes: u64, ram_bytes: u64) -> bool {
        if entry_pa & 3 != 0
            || device_tree_pa & 7 != 0
            || device_tree_bytes == 0
            || device_tree_pa.checked_add(device_tree_bytes).is_none()
            || device_tree_pa.checked_add(device_tree_bytes).unwrap_or(u64::MAX) > ram_bytes
        {
            return false;
        }
        self.entry_pa = entry_pa;
        self.device_tree_pa = device_tree_pa;
        self.device_tree_bytes = device_tree_bytes;
        self.prepared = true;
        self.signature_verified = false;
        true
    }

    fn reset(&mut self) {
        *self = Self::initial();
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1DmaAccess {
    DeviceReadGuest = DMA_READ as isize,
    DeviceWriteGuest = DMA_WRITE as isize,
    Bidirectional = (DMA_READ | DMA_WRITE) as isize,
}

impl M1DmaAccess {
    fn bits(self) -> u8 {
        match self {
            Self::DeviceReadGuest => DMA_READ,
            Self::DeviceWriteGuest => DMA_WRITE,
            Self::Bidirectional => DMA_READ | DMA_WRITE,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1DmaFault {
    InvalidArguments,
    Unmapped,
    Permission,
    Overlap,
    Bounds,
    TableFull,
}

#[derive(Clone, Copy)]
struct M1DartMapping {
    valid: bool,
    stream_id: u16,
    iova: u64,
    pa: u64,
    bytes: u64,
    permissions: u8,
}

const EMPTY_DART_MAPPING: M1DartMapping = M1DartMapping {
    valid: false,
    stream_id: 0,
    iova: 0,
    pa: 0,
    bytes: 0,
    permissions: 0,
};

/// A bounded DART-style translation table.  It is a semantic DMA boundary,
/// not an assertion that these array entries are Apple's physical DART page
/// tables.  Device accesses must go through `dma_read`/`dma_write`, so a
/// mapped IOVA cannot silently become an unrestricted guest RAM offset.
pub(crate) struct M1Dart {
    mappings: [M1DartMapping; M1_MAX_DART_MAPPINGS],
    mapping_count: u32,
    ram_bytes: u64,
    generation: u32,
}

impl M1Dart {
    fn new(ram_bytes: u64) -> Self {
        Self {
            mappings: [EMPTY_DART_MAPPING; M1_MAX_DART_MAPPINGS],
            mapping_count: 0,
            ram_bytes,
            generation: 0,
        }
    }

    fn reset(&mut self) {
        self.mappings = [EMPTY_DART_MAPPING; M1_MAX_DART_MAPPINGS];
        self.mapping_count = 0;
        self.generation = self.generation.saturating_add(1);
    }

    fn map(
        &mut self,
        stream_id: u16,
        iova: u64,
        pa: u64,
        bytes: u64,
        access: M1DmaAccess,
    ) -> Result<(), M1DmaFault> {
        if bytes == 0
            || iova & (M1_DART_GRANULE - 1) != 0
            || pa & (M1_DART_GRANULE - 1) != 0
            || bytes & (M1_DART_GRANULE - 1) != 0
            || iova.checked_add(bytes).is_none()
            || pa.checked_add(bytes).is_none()
            || pa.checked_add(bytes).unwrap_or(u64::MAX) > self.ram_bytes
        {
            return Err(M1DmaFault::InvalidArguments);
        }
        if self
            .mappings
            .iter()
            .any(|mapping| {
                mapping.valid
                    && mapping.stream_id == stream_id
                    && ranges_overlap(mapping.iova, mapping.bytes, iova, bytes)
            })
        {
            return Err(M1DmaFault::Overlap);
        }
        let Some(slot) = self.mappings.iter_mut().find(|mapping| !mapping.valid) else {
            return Err(M1DmaFault::TableFull);
        };
        *slot = M1DartMapping {
            valid: true,
            stream_id,
            iova,
            pa,
            bytes,
            permissions: access.bits(),
        };
        self.mapping_count = self.mapping_count.saturating_add(1);
        self.generation = self.generation.saturating_add(1);
        Ok(())
    }

    fn unmap(&mut self, stream_id: u16, iova: u64, bytes: u64) -> bool {
        let Some(mapping) = self.mappings.iter_mut().find(|mapping| {
            mapping.valid
                && mapping.stream_id == stream_id
                && mapping.iova == iova
                && mapping.bytes == bytes
        }) else {
            return false;
        };
        *mapping = EMPTY_DART_MAPPING;
        self.mapping_count = self.mapping_count.saturating_sub(1);
        self.generation = self.generation.saturating_add(1);
        true
    }

    fn translate(
        &self,
        stream_id: u16,
        iova: u64,
        bytes: u64,
        access: M1DmaAccess,
    ) -> Result<u64, M1DmaFault> {
        if bytes == 0 {
            return Err(M1DmaFault::InvalidArguments);
        }
        let Some(mapping) = self
            .mappings
            .iter()
            .find(|mapping| {
                mapping.valid
                    && mapping.stream_id == stream_id
                    && iova >= mapping.iova
                    && iova.checked_add(bytes).is_some()
                    && iova.checked_add(bytes).unwrap_or(u64::MAX)
                        <= mapping.iova.saturating_add(mapping.bytes)
            })
        else {
            return Err(M1DmaFault::Unmapped);
        };
        if mapping.permissions & access.bits() != access.bits() {
            return Err(M1DmaFault::Permission);
        }
        mapping
            .pa
            .checked_add(iova - mapping.iova)
            .ok_or(M1DmaFault::Bounds)
    }

    fn dma_read(
        &self,
        stream_id: u16,
        iova: u64,
        destination: &mut [u8],
        guest_ram: &[u8],
    ) -> Result<(), M1DmaFault> {
        let pa = self.translate(
            stream_id,
            iova,
            destination.len() as u64,
            M1DmaAccess::DeviceReadGuest,
        )?;
        let range = byte_range(pa, destination.len(), guest_ram.len())?;
        destination.copy_from_slice(&guest_ram[range.0..range.1]);
        Ok(())
    }

    fn dma_write(
        &self,
        stream_id: u16,
        iova: u64,
        source: &[u8],
        guest_ram: &mut [u8],
    ) -> Result<(), M1DmaFault> {
        let pa = self.translate(
            stream_id,
            iova,
            source.len() as u64,
            M1DmaAccess::DeviceWriteGuest,
        )?;
        let range = byte_range(pa, source.len(), guest_ram.len())?;
        guest_ram[range.0..range.1].copy_from_slice(source);
        Ok(())
    }

    fn valid(&self) -> bool {
        self.mapping_count as usize <= M1_MAX_DART_MAPPINGS
            && self.ram_bytes != 0
            && self
                .mappings
                .iter()
                .filter(|mapping| mapping.valid)
                .count()
                == self.mapping_count as usize
    }
}

#[derive(Clone, Copy)]
pub(crate) struct M1Aic {
    pending: u64,
    enabled: u64,
    targets: [u64; M1_INTERRUPT_SOURCES],
}

impl M1Aic {
    const fn reset() -> Self {
        Self {
            pending: 0,
            enabled: u64::MAX,
            targets: [1; M1_INTERRUPT_SOURCES],
        }
    }

    fn valid_source(source: u8) -> bool {
        (source as usize) < M1_INTERRUPT_SOURCES
    }

    fn enable(&mut self, source: u8, enabled: bool) -> bool {
        if !Self::valid_source(source) {
            return false;
        }
        let bit = 1u64 << source;
        if enabled {
            self.enabled |= bit;
        } else {
            self.enabled &= !bit;
        }
        true
    }

    fn route(&mut self, source: u8, cpu_mask: u64) -> bool {
        if !Self::valid_source(source) || cpu_mask == 0 {
            return false;
        }
        self.targets[source as usize] = cpu_mask;
        true
    }

    fn raise(&mut self, source: u8) -> bool {
        if !Self::valid_source(source) {
            return false;
        }
        self.pending |= 1u64 << source;
        true
    }

    fn take(&self, cpu: u32) -> Option<u8> {
        if cpu >= 64 {
            return None;
        }
        let cpu_bit = 1u64 << cpu;
        (0..M1_INTERRUPT_SOURCES).find_map(|source| {
            let bit = 1u64 << source;
            (self.pending & bit != 0
                && self.enabled & bit != 0
                && self.targets[source] & cpu_bit != 0)
                .then_some(source as u8)
        })
    }

    fn take_non_timer(&self, cpu: u32) -> Option<u8> {
        if cpu >= 64 {
            return None;
        }
        let cpu_bit = 1u64 << cpu;
        (0..M1_INTERRUPT_SOURCES).filter(|source| *source != TIMER_SOURCE as usize).find_map(|source| {
            let bit = 1u64 << source;
            (self.pending & bit != 0
                && self.enabled & bit != 0
                && self.targets[source] & cpu_bit != 0)
                .then_some(source as u8)
        })
    }

    fn acknowledge(&mut self, source: u8) -> bool {
        if !Self::valid_source(source) || self.pending & (1u64 << source) == 0 {
            return false;
        }
        self.pending &= !(1u64 << source);
        true
    }

    fn pending(&self) -> u64 {
        self.pending
    }
}

#[derive(Clone, Copy)]
pub(crate) struct M1Timer {
    pub(crate) frequency: u64,
    pub(crate) counter: u64,
    pub(crate) compare: u64,
    pub(crate) enabled: bool,
    pub(crate) masked: bool,
}

impl M1Timer {
    const fn reset() -> Self {
        Self {
            frequency: M1_COUNTER_FREQUENCY,
            counter: 0,
            compare: 0,
            enabled: false,
            masked: false,
        }
    }

    fn pending(&self) -> bool {
        self.enabled && !self.masked && self.counter >= self.compare
    }

    fn advance(&mut self, ticks: u64) {
        self.counter = self.counter.saturating_add(ticks);
    }

    fn program(&mut self, compare: u64, enabled: bool, masked: bool) {
        self.compare = compare;
        self.enabled = enabled;
        self.masked = masked;
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1StorageFault {
    NotAttached,
    InvalidBlock,
    BackendBounds,
    ReadOnly,
}

pub(crate) struct M1Storage {
    pub(crate) attached: bool,
    pub(crate) read_only: bool,
    pub(crate) block_count: u64,
    pub(crate) generation: u32,
}

impl M1Storage {
    const fn reset() -> Self {
        Self {
            attached: false,
            read_only: false,
            block_count: 0,
            generation: 0,
        }
    }

    fn attach(&mut self, block_count: u64, read_only: bool) -> bool {
        if block_count == 0
            || block_count
                .checked_mul(M1_STORAGE_BLOCK_BYTES as u64)
                .is_none()
        {
            return false;
        }
        self.attached = true;
        self.read_only = read_only;
        self.block_count = block_count;
        self.generation = self.generation.saturating_add(1);
        true
    }

    fn reset_runtime(&mut self) {
        *self = Self::reset();
    }

    fn backend_range(&self, block: u64, backend_len: usize) -> Result<(usize, usize), M1StorageFault> {
        if !self.attached {
            return Err(M1StorageFault::NotAttached);
        }
        if block >= self.block_count {
            return Err(M1StorageFault::InvalidBlock);
        }
        let start = block
            .checked_mul(M1_STORAGE_BLOCK_BYTES as u64)
            .and_then(|value| usize::try_from(value).ok())
            .ok_or(M1StorageFault::BackendBounds)?;
        let end = start
            .checked_add(M1_STORAGE_BLOCK_BYTES)
            .ok_or(M1StorageFault::BackendBounds)?;
        if end > backend_len {
            return Err(M1StorageFault::BackendBounds);
        }
        Ok((start, end))
    }

    fn read(
        &self,
        block: u64,
        backend: &[u8],
        destination: &mut [u8],
    ) -> Result<(), M1StorageFault> {
        if destination.len() != M1_STORAGE_BLOCK_BYTES {
            return Err(M1StorageFault::BackendBounds);
        }
        let range = self.backend_range(block, backend.len())?;
        destination.copy_from_slice(&backend[range.0..range.1]);
        Ok(())
    }

    fn write(
        &self,
        block: u64,
        source: &[u8],
        backend: &mut [u8],
    ) -> Result<(), M1StorageFault> {
        if self.read_only {
            return Err(M1StorageFault::ReadOnly);
        }
        if source.len() != M1_STORAGE_BLOCK_BYTES {
            return Err(M1StorageFault::BackendBounds);
        }
        let range = self.backend_range(block, backend.len())?;
        backend[range.0..range.1].copy_from_slice(source);
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1DisplayFormat {
    Xrgb8888 = 1,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1DisplayFault {
    InvalidMode,
    UnsupportedFormat,
    NotConfigured,
    InvalidRegister,
}

pub(crate) struct M1Framebuffer {
    pub(crate) guest_address: u64,
    pub(crate) backing_bytes: u64,
    pub(crate) width: u32,
    pub(crate) height: u32,
    pub(crate) stride: u32,
    pub(crate) format: Option<M1DisplayFormat>,
    pub(crate) enabled: bool,
    pub(crate) presented: bool,
    pub(crate) frame_count: u64,
    pub(crate) generation: u32,
}

impl M1Framebuffer {
    const fn reset() -> Self {
        Self {
            guest_address: 0,
            backing_bytes: 0,
            width: 0,
            height: 0,
            stride: 0,
            format: None,
            enabled: false,
            presented: false,
            frame_count: 0,
            generation: 0,
        }
    }

    fn configured(&self) -> bool {
        self.format.is_some() && self.width != 0 && self.height != 0 && self.backing_bytes != 0
    }

    fn configure(
        &mut self,
        guest_address: u64,
        backing_bytes: u64,
        width: u32,
        height: u32,
        stride: u32,
        format: M1DisplayFormat,
    ) -> Result<(), M1DisplayFault> {
        let required = u64::from(stride)
            .checked_mul(u64::from(height))
            .ok_or(M1DisplayFault::InvalidMode)?;
        if guest_address & 7 != 0
            || backing_bytes == 0
            || width == 0
            || height == 0
            || width > M1_MAX_DISPLAY_WIDTH
            || height > M1_MAX_DISPLAY_HEIGHT
            || stride < width.saturating_mul(4)
            || required > backing_bytes
        {
            return Err(M1DisplayFault::InvalidMode);
        }
        if !matches!(format, M1DisplayFormat::Xrgb8888) {
            return Err(M1DisplayFault::UnsupportedFormat);
        }
        self.guest_address = guest_address;
        self.backing_bytes = backing_bytes;
        self.width = width;
        self.height = height;
        self.stride = stride;
        self.format = Some(format);
        self.enabled = false;
        self.presented = false;
        self.generation = self.generation.saturating_add(1);
        Ok(())
    }

    fn present(&mut self) -> Result<(), M1DisplayFault> {
        if !self.configured() {
            return Err(M1DisplayFault::NotConfigured);
        }
        self.enabled = true;
        self.presented = true;
        self.frame_count = self.frame_count.saturating_add(1);
        Ok(())
    }

    fn read_mmio(&self, offset: u64, width: u32) -> Option<u64> {
        if width != 4 {
            return None;
        }
        match offset {
            0x00 => Some((self.configured() as u32 | ((self.enabled as u32) << 1) | ((self.presented as u32) << 2)) as u64),
            0x04 => Some(u64::from(self.width)),
            0x08 => Some(u64::from(self.height)),
            0x0c => Some(u64::from(self.stride)),
            0x10 => Some(self.frame_count),
            _ => None,
        }
    }

    fn write_mmio(&mut self, offset: u64, width: u32, value: u64) -> Result<(), M1DisplayFault> {
        if width != 4 || offset != 0x00 {
            return Err(M1DisplayFault::InvalidRegister);
        }
        match value as u32 {
            0 => {
                self.enabled = false;
                Ok(())
            }
            1 => self.present(),
            _ => Err(M1DisplayFault::InvalidRegister),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum M1RecoveryFault {
    ShortFrame,
    BadMagic,
    BadLength,
    BadChecksum,
    Sequence,
    PayloadTooLarge,
    OutputTooSmall,
}

/// Internal bounded envelope for recovery data.  The envelope carries opaque
/// bytes and a CRC for transport integrity; `signature_verified` remains false
/// until an external Apple trust-chain verifier supplies evidence.
pub(crate) struct M1RecoveryTransport {
    expected_sequence: u32,
    last_sequence: u32,
    flags: u32,
    payload: [u8; M1_MAX_RECOVERY_PAYLOAD],
    payload_len: usize,
    ready: bool,
    signature_verified: bool,
}

impl M1RecoveryTransport {
    const fn reset() -> Self {
        Self {
            expected_sequence: 0,
            last_sequence: 0,
            flags: 0,
            payload: [0; M1_MAX_RECOVERY_PAYLOAD],
            payload_len: 0,
            ready: false,
            signature_verified: false,
        }
    }

    fn encode(sequence: u32, flags: u32, payload: &[u8], output: &mut [u8]) -> Result<usize, M1RecoveryFault> {
        if payload.len() > M1_MAX_RECOVERY_PAYLOAD {
            return Err(M1RecoveryFault::PayloadTooLarge);
        }
        let total = M1_RECOVERY_HEADER_BYTES
            .checked_add(payload.len())
            .ok_or(M1RecoveryFault::PayloadTooLarge)?;
        if output.len() < total {
            return Err(M1RecoveryFault::OutputTooSmall);
        }
        put_u32(&mut output[0..4], RECOVERY_MAGIC);
        put_u32(&mut output[4..8], sequence);
        put_u32(&mut output[8..12], flags);
        put_u32(&mut output[12..16], payload.len() as u32);
        put_u32(&mut output[16..20], crc32(payload));
        output[M1_RECOVERY_HEADER_BYTES..total].copy_from_slice(payload);
        Ok(total)
    }

    fn ingest(&mut self, frame: &[u8]) -> Result<usize, M1RecoveryFault> {
        if frame.len() < M1_RECOVERY_HEADER_BYTES {
            return Err(M1RecoveryFault::ShortFrame);
        }
        if read_u32(&frame[0..4]) != RECOVERY_MAGIC {
            return Err(M1RecoveryFault::BadMagic);
        }
        let sequence = read_u32(&frame[4..8]);
        let flags = read_u32(&frame[8..12]);
        let payload_len = read_u32(&frame[12..16]) as usize;
        if payload_len > M1_MAX_RECOVERY_PAYLOAD {
            return Err(M1RecoveryFault::PayloadTooLarge);
        }
        let total = M1_RECOVERY_HEADER_BYTES
            .checked_add(payload_len)
            .ok_or(M1RecoveryFault::BadLength)?;
        if frame.len() != total {
            return Err(M1RecoveryFault::BadLength);
        }
        let payload = &frame[M1_RECOVERY_HEADER_BYTES..total];
        if read_u32(&frame[16..20]) != crc32(payload) {
            return Err(M1RecoveryFault::BadChecksum);
        }
        if sequence != self.expected_sequence {
            return Err(M1RecoveryFault::Sequence);
        }
        self.payload[..payload_len].copy_from_slice(payload);
        self.payload_len = payload_len;
        self.flags = flags;
        self.last_sequence = sequence;
        self.expected_sequence = self.expected_sequence.wrapping_add(1);
        self.ready = true;
        self.signature_verified = false;
        Ok(payload_len)
    }

    fn payload(&self) -> &[u8] {
        &self.payload[..self.payload_len]
    }

    fn reset_runtime(&mut self) {
        *self = Self::reset();
    }
}

const RECOVERY_MAGIC: u32 = u32::from_le_bytes(*b"VFR1");

fn put_u32(destination: &mut [u8], value: u32) {
    destination.copy_from_slice(&value.to_le_bytes());
}

fn read_u32(source: &[u8]) -> u32 {
    u32::from_le_bytes([source[0], source[1], source[2], source[3]])
}

fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = 0xffff_ffffu32;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            let mask = 0u32.wrapping_sub(crc & 1);
            crc = (crc >> 1) ^ (0xedb8_8320 & mask);
        }
    }
    !crc
}

fn byte_range(address: u64, bytes: usize, limit: usize) -> Result<(usize, usize), M1DmaFault> {
    let start = usize::try_from(address).map_err(|_| M1DmaFault::Bounds)?;
    let end = start.checked_add(bytes).ok_or(M1DmaFault::Bounds)?;
    if end > limit {
        return Err(M1DmaFault::Bounds);
    }
    Ok((start, end))
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

/// Native M1 graph.  All child components reset synchronously with this
/// object, so a future EFI handoff cannot observe a half-reset device set.
pub(crate) struct M1MachineGraph {
    pub(crate) identity: M1FirmwareIdentity,
    pub(crate) ram_bytes: u64,
    devices: [M1DeviceDescriptor; M1_MAX_DEVICES],
    device_count: u32,
    pub(crate) aic: M1Aic,
    pub(crate) timer: M1Timer,
    pub(crate) dart: M1Dart,
    pub(crate) storage: M1Storage,
    pub(crate) recovery: M1RecoveryTransport,
    pub(crate) display: M1Framebuffer,
    pub(crate) handoff: M1FirmwareHandoff,
    pub(crate) reset_generation: u32,
    pub(crate) runtime_active: bool,
    uart_last_byte: u8,
}

impl M1MachineGraph {
    pub(crate) fn new(ram_bytes: u64) -> Self {
        let mut graph = Self {
            identity: M1FirmwareIdentity::t8103(),
            ram_bytes,
            devices: [EMPTY_DEVICE; M1_MAX_DEVICES],
            device_count: 0,
            aic: M1Aic::reset(),
            timer: M1Timer::reset(),
            dart: M1Dart::new(ram_bytes),
            storage: M1Storage::reset(),
            recovery: M1RecoveryTransport::reset(),
            display: M1Framebuffer::reset(),
            handoff: M1FirmwareHandoff::initial(),
            reset_generation: 0,
            runtime_active: false,
            uart_last_byte: 0,
        };
        let kinds = [
            M1DeviceKind::Firmware,
            M1DeviceKind::Aic,
            M1DeviceKind::Timer,
            M1DeviceKind::Dart,
            M1DeviceKind::Storage,
            M1DeviceKind::Recovery,
            M1DeviceKind::Display,
            M1DeviceKind::Uart,
        ];
        for kind in kinds {
            graph.devices[graph.device_count as usize] = M1DeviceDescriptor {
                kind,
                instance: 0,
                contract_ready: true,
                guest_visible: true,
            };
            graph.device_count += 1;
        }
        graph.reset();
        graph
    }

    pub(crate) fn reset(&mut self) {
        self.aic = M1Aic::reset();
        self.timer = M1Timer::reset();
        self.dart.reset();
        self.storage.reset_runtime();
        self.recovery.reset_runtime();
        self.display = M1Framebuffer::reset();
        self.handoff.reset();
        self.runtime_active = false;
        self.uart_last_byte = 0;
        self.reset_generation = self.reset_generation.saturating_add(1);
    }

    /// Activate the fixed M1 graph inside the current EFI/preOS call.
    ///
    /// This is deliberately a graph activation, not a claim that physical
    /// Apple register programming or a signed firmware handoff has occurred.
    /// It wires the contract-backed interrupt sources to CPU0 and leaves
    /// storage/display/recovery payloads caller-owned until their respective
    /// inputs are attached.
    pub(crate) fn activate_runtime(&mut self) -> bool {
        if !self.valid() {
            return false;
        }
        for source in [TIMER_SOURCE, STORAGE_SOURCE, DISPLAY_SOURCE, RECOVERY_SOURCE] {
            if !self.route_interrupt(source, 1) || !self.enable_interrupt(source, true) {
                return false;
            }
        }
        self.runtime_active = true;
        true
    }

    /// Mirror the architectural generic timer into the M1 graph after one
    /// retired guest instruction.  The graph's AIC pending bit is kept in
    /// sync, while the architectural core remains the authority that turns
    /// the timer condition into a guest exception.
    pub(crate) fn sync_guest_timer(&mut self, counter: u64, ctl: u64, cval: u64) -> bool {
        if !self.runtime_active {
            return false;
        }
        self.timer.counter = counter;
        self.timer.program(cval, ctl & 1 != 0, ctl & (1 << 1) != 0);
        if self.timer.pending() {
            let _ = self.aic.raise(TIMER_SOURCE);
        } else if self.aic.pending() & (1u64 << TIMER_SOURCE) != 0 {
            let _ = self.aic.acknowledge(TIMER_SOURCE);
        }
        true
    }

    pub(crate) fn tick(&mut self, ticks: u64) {
        self.timer.advance(ticks);
        if self.timer.pending() {
            let _ = self.aic.raise(TIMER_SOURCE);
        }
    }

    pub(crate) fn program_timer(&mut self, compare: u64, enabled: bool, masked: bool) {
        self.timer.program(compare, enabled, masked);
        if !self.timer.pending() {
            let _ = self.aic.acknowledge(TIMER_SOURCE);
        }
    }

    pub(crate) fn route_interrupt(&mut self, source: u8, cpu_mask: u64) -> bool {
        self.aic.route(source, cpu_mask)
    }

    pub(crate) fn enable_interrupt(&mut self, source: u8, enabled: bool) -> bool {
        self.aic.enable(source, enabled)
    }

    pub(crate) fn raise_interrupt(&mut self, source: u8) -> bool {
        self.aic.raise(source)
    }

    pub(crate) fn take_interrupt(&self, cpu: u32) -> Option<u8> {
        self.aic.take(cpu)
    }

    pub(crate) fn acknowledge_interrupt(&mut self, source: u8) -> bool {
        self.aic.acknowledge(source)
    }

    pub(crate) fn map_dma(
        &mut self,
        stream_id: u16,
        iova: u64,
        pa: u64,
        bytes: u64,
        access: M1DmaAccess,
    ) -> Result<(), M1DmaFault> {
        self.dart.map(stream_id, iova, pa, bytes, access)
    }

    pub(crate) fn unmap_dma(&mut self, stream_id: u16, iova: u64, bytes: u64) -> bool {
        self.dart.unmap(stream_id, iova, bytes)
    }

    pub(crate) fn dma_read(
        &self,
        stream_id: u16,
        iova: u64,
        destination: &mut [u8],
        guest_ram: &[u8],
    ) -> Result<(), M1DmaFault> {
        self.dart.dma_read(stream_id, iova, destination, guest_ram)
    }

    pub(crate) fn dma_write(
        &self,
        stream_id: u16,
        iova: u64,
        source: &[u8],
        guest_ram: &mut [u8],
    ) -> Result<(), M1DmaFault> {
        self.dart.dma_write(stream_id, iova, source, guest_ram)
    }

    pub(crate) fn attach_storage(&mut self, block_count: u64, read_only: bool) -> bool {
        self.storage.attach(block_count, read_only)
    }

    pub(crate) fn configure_display(
        &mut self,
        guest_address: u64,
        backing_bytes: u64,
        width: u32,
        height: u32,
        stride: u32,
        format: M1DisplayFormat,
    ) -> Result<(), M1DisplayFault> {
        self.display
            .configure(guest_address, backing_bytes, width, height, stride, format)
    }

    pub(crate) fn present_display(&mut self) -> Result<(), M1DisplayFault> {
        let result = self.display.present();
        if result.is_ok() {
            let _ = self.aic.raise(DISPLAY_SOURCE);
        }
        result
    }

    pub(crate) fn configure_handoff(
        &mut self,
        entry_pa: u64,
        device_tree_pa: u64,
        device_tree_bytes: u64,
    ) -> bool {
        self.handoff
            .prepare(entry_pa, device_tree_pa, device_tree_bytes, self.ram_bytes)
    }

    pub(crate) fn ingest_recovery(&mut self, frame: &[u8]) -> Result<usize, M1RecoveryFault> {
        let result = self.recovery.ingest(frame);
        if result.is_ok() {
            let _ = self.aic.raise(RECOVERY_SOURCE);
        }
        result
    }

    pub(crate) fn recovery_payload(&self) -> &[u8] {
        self.recovery.payload()
    }

    pub(crate) fn display_mmio_read(&self, offset: u64, width: u32) -> Option<u64> {
        self.display.read_mmio(offset, width)
    }

    pub(crate) fn display_mmio_write(
        &mut self,
        offset: u64,
        width: u32,
        value: u64,
    ) -> Result<(), M1DisplayFault> {
        let result = self.display.write_mmio(offset, width, value);
        if result.is_ok() && offset == 0 && value == 1 {
            let _ = self.aic.raise(DISPLAY_SOURCE);
        }
        result
    }

    /// Dispatch a graph-local MMIO access.  The windows are an internal
    /// address-space contract for the native machine graph; they are not the
    /// physical Apple register map.  Unhandled registers and widths fail
    /// closed so a caller cannot accidentally turn this into unrestricted
    /// memory access.
    pub(crate) fn mmio_read(&self, address: u64, width: u32) -> Result<u64, M1MmioFault> {
        let (window, offset) = logical_window(address, width)?;
        match window {
            M1LogicalWindow::Firmware => {
                mmio_width(width, 32)?;
                match offset {
                    0x00 => Ok(u64::from(self.identity.soc_id)),
                    0x04 => Ok(u64::from(self.identity.cpu_count)),
                    0x08 => Ok(u64::from(self.identity.aarch64 as u8 | ((self.identity.macos_only as u8) << 1))),
                    0x0c => Ok(u64::from(self.handoff.prepared as u8 | ((self.handoff.signature_verified as u8) << 1))),
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
            M1LogicalWindow::Aic => {
                match offset {
                    0x00 => { mmio_width(width, 64)?; Ok(self.aic.pending()) }
                    0x08 => { mmio_width(width, 64)?; Ok(self.aic.enabled) }
                    0x10 => { mmio_width(width, 32)?; Ok(u64::from(self.aic.targets[0] as u32)) }
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
            M1LogicalWindow::Timer => match offset {
                0x00 => { mmio_width(width, 64)?; Ok(self.timer.counter) }
                0x08 => { mmio_width(width, 64)?; Ok(self.timer.compare) }
                0x10 => { mmio_width(width, 32)?; Ok(u64::from(self.timer.enabled as u8 | ((self.timer.masked as u8) << 1))) }
                0x18 => { mmio_width(width, 64)?; Ok(self.timer.frequency) }
                _ => Err(M1MmioFault::InvalidRegister),
            },
            M1LogicalWindow::Dart => {
                mmio_width(width, 32)?;
                match offset {
                    0x00 => Ok(u64::from(self.dart.mapping_count)),
                    0x04 => Ok(u64::from(self.dart.generation)),
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
            M1LogicalWindow::Storage => {
                mmio_width(width, 64)?;
                match offset {
                    0x00 => Ok(u64::from(self.storage.attached as u8 | ((self.storage.read_only as u8) << 1))),
                    0x08 => Ok(self.storage.block_count),
                    0x10 => Ok(u64::from(self.storage.generation)),
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
            M1LogicalWindow::Recovery => {
                mmio_width(width, 32)?;
                match offset {
                    0x00 => Ok(u64::from(self.recovery.ready as u8 | ((self.recovery.signature_verified as u8) << 1))),
                    0x04 => Ok(u64::from(self.recovery.last_sequence)),
                    0x08 => Ok(self.recovery.payload_len as u64),
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
            M1LogicalWindow::Display => self.display_mmio_read(offset, width / 8).ok_or(
                if width != 32 { M1MmioFault::InvalidWidth } else { M1MmioFault::InvalidRegister },
            ),
            M1LogicalWindow::Uart => {
                mmio_width(width, 32)?;
                match offset {
                    0x00 => Ok(u64::from(self.uart_last_byte)),
                    0x04 => Ok(1), // logical TX-ready status
                    _ => Err(M1MmioFault::InvalidRegister),
                }
            }
        }
    }

    pub(crate) fn mmio_write(
        &mut self,
        address: u64,
        width: u32,
        value: u64,
    ) -> Result<(), M1MmioFault> {
        let (window, offset) = logical_window(address, width)?;
        match window {
            M1LogicalWindow::Firmware | M1LogicalWindow::Storage | M1LogicalWindow::Recovery => Err(M1MmioFault::ReadOnly),
            M1LogicalWindow::Aic => match offset {
                0x08 => {
                    mmio_width(width, 64)?;
                    let valid_bits = (1u64 << M1_INTERRUPT_SOURCES) - 1;
                    if value & !valid_bits != 0 {
                        return Err(M1MmioFault::InvalidRegister);
                    }
                    self.aic.enabled = value;
                    Ok(())
                }
                0x10 => {
                    mmio_width(width, 32)?;
                    let source = value as u8;
                    self.acknowledge_interrupt(source).then_some(()).ok_or(M1MmioFault::InvalidRegister)
                }
                0x18 => {
                    mmio_width(width, 64)?;
                    let source = (value & 0xff) as u8;
                    let cpu_mask = value >> 8;
                    let valid_cpu_mask = (1u64 << M1_CPU_COUNT) - 1;
                    if cpu_mask == 0 || cpu_mask & !valid_cpu_mask != 0 {
                        return Err(M1MmioFault::InvalidRegister);
                    }
                    self.route_interrupt(source, cpu_mask).then_some(()).ok_or(M1MmioFault::InvalidRegister)
                }
                _ => Err(M1MmioFault::InvalidRegister),
            },
            M1LogicalWindow::Timer => match offset {
                0x08 => { mmio_width(width, 64)?; self.program_timer(value, self.timer.enabled, self.timer.masked); Ok(()) }
                0x10 => {
                    mmio_width(width, 32)?;
                    if value & !3 != 0 { return Err(M1MmioFault::InvalidRegister); }
                    self.program_timer(self.timer.compare, value & 1 != 0, value & 2 != 0);
                    Ok(())
                }
                _ => Err(M1MmioFault::ReadOnly),
            },
            M1LogicalWindow::Dart => {
                mmio_width(width, 32)?;
                if offset == 0x08 && value == 1 {
                    self.dart.reset();
                    Ok(())
                } else {
                    Err(M1MmioFault::InvalidRegister)
                }
            }
            M1LogicalWindow::Display => self.display_mmio_write(offset, width / 8, value).map_err(|_| {
                if width != 32 { M1MmioFault::InvalidWidth } else { M1MmioFault::InvalidRegister }
            }),
            M1LogicalWindow::Uart => {
                mmio_width(width, 32)?;
                if offset != 0 || value > 0xff { return Err(M1MmioFault::InvalidRegister); }
                self.uart_last_byte = value as u8;
                Ok(())
            }
        }
    }

    pub(crate) fn device_ready(&self, kind: M1DeviceKind) -> bool {
        self.devices[..self.device_count as usize]
            .iter()
            .any(|device| device.kind == kind && device.contract_ready && device.guest_visible)
    }

    pub(crate) fn valid(&self) -> bool {
        self.identity.valid()
            && self.ram_bytes != 0
            && self.device_count == M1_MAX_DEVICES as u32
            && self
                .devices
                .iter()
                .all(|device| device.contract_ready && device.guest_visible)
            && self.dart.valid()
            && self.timer.frequency == M1_COUNTER_FREQUENCY
            && self.reset_generation != 0
            && !self.handoff.signature_verified
            && !self.recovery.signature_verified
    }
}

fn guest_mmio_logical(address: u64, size: usize) -> Option<u64> {
    let bytes = u64::try_from(size).ok()?;
    let end = address.checked_add(bytes)?;
    let limit = M1_GUEST_MMIO_BASE.checked_add(M1_GUEST_MMIO_BYTES)?;
    if address >= M1_GUEST_MMIO_BASE && end <= limit {
        Some(address - M1_GUEST_MMIO_BASE)
    } else {
        None
    }
}

fn mmio_fault_exception(fault: M1MmioFault) -> ExceptionKind {
    match fault {
        M1MmioFault::ReadOnly => ExceptionKind::PermissionFault,
        M1MmioFault::Unmapped
        | M1MmioFault::OutOfRange
        | M1MmioFault::InvalidWidth
        | M1MmioFault::InvalidRegister
        | M1MmioFault::Unsupported => ExceptionKind::DataAbort,
    }
}

fn bus_read_width(memory: &[u8], index: usize, width: usize) -> Option<u64> {
    let bytes = memory.get(index..index.checked_add(width)?)?;
    let mut value = 0u64;
    for (shift, byte) in bytes.iter().enumerate() {
        value |= u64::from(*byte) << (shift * 8);
    }
    Some(value)
}

fn bus_write_width(memory: &mut [u8], index: usize, width: usize, value: u64) -> bool {
    let Some(bytes) = memory.get_mut(index..index.saturating_add(width)) else {
        return false;
    };
    for (shift, byte) in bytes.iter_mut().enumerate() {
        *byte = (value >> (shift * 8)) as u8;
    }
    true
}

/// Adapter from the architectural core to the native M1 graph.
///
/// RAM accesses use the same bounded byte slice as the earlier reference
/// core.  Only the high Venfire alias is dispatched to graph-local MMIO, so a
/// guest cannot turn an arbitrary address into a device access.  The graph is
/// also notified after each committed instruction to keep its timer/AIC view
/// synchronized with the architectural counter.
pub(crate) struct M1GuestBus<'a> {
    graph: &'a mut M1MachineGraph,
    ram: &'a mut [u8],
    timer_mmio_dirty: bool,
}

impl<'a> M1GuestBus<'a> {
    pub(crate) fn new(graph: &'a mut M1MachineGraph, ram: &'a mut [u8]) -> Self {
        Self {
            graph,
            ram,
            timer_mmio_dirty: false,
        }
    }
}

impl GuestBus for M1GuestBus<'_> {
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
        access: Access,
    ) -> Result<u64, ExceptionKind> {
        if !matches!(size, 1 | 2 | 4 | 8) {
            return Err(ExceptionKind::AlignmentFault);
        }
        if let Some(logical) = guest_mmio_logical(address, size) {
            if address & (size as u64 - 1) != 0 {
                return Err(ExceptionKind::AlignmentFault);
            }
            if access == Access::Execute {
                return Err(ExceptionKind::PermissionFault);
            }
            return self
                .graph
                .mmio_read(logical, (size * 8) as u32)
                .map_err(mmio_fault_exception);
        }
        bus_read_width(
            self.ram,
            usize::try_from(address).map_err(|_| ExceptionKind::DataAbort)?,
            size,
        )
        .ok_or(ExceptionKind::DataAbort)
    }

    fn write(
        &mut self,
        address: u64,
        size: usize,
        value: u64,
        access: Access,
    ) -> Result<(), ExceptionKind> {
        if access != Access::Write || !matches!(size, 1 | 2 | 4 | 8) {
            return Err(ExceptionKind::PermissionFault);
        }
        if let Some(logical) = guest_mmio_logical(address, size) {
            if address & (size as u64 - 1) != 0 {
                return Err(ExceptionKind::AlignmentFault);
            }
            let result = self
                .graph
                .mmio_write(logical, (size * 8) as u32, value)
                .map_err(mmio_fault_exception);
            if result.is_ok()
                && (logical == M1_LOGICAL_TIMER_BASE + 0x08
                    || logical == M1_LOGICAL_TIMER_BASE + 0x10)
            {
                self.timer_mmio_dirty = true;
            }
            return result;
        }
        let index = usize::try_from(address).map_err(|_| ExceptionKind::DataAbort)?;
        bus_write_width(self.ram, index, size, value)
            .then_some(())
            .ok_or(ExceptionKind::DataAbort)
    }

    fn after_instruction(&mut self, state: &mut GuestCpuState) {
        if self.timer_mmio_dirty {
            // A guest timer MMIO write is the device-side programming path.
            // Reflect it into the architectural bank before the next guest
            // boundary, otherwise the ordinary state-to-device mirror would
            // immediately overwrite the newly programmed compare value.
            state.timer.cval = self.graph.timer.compare;
            state.timer.ctl = u64::from(self.graph.timer.enabled)
                | (u64::from(self.graph.timer.masked) << 1);
            state.sys.cntp_cval_el0 = state.timer.cval;
            state.sys.cntp_ctl_el0 = state.timer.ctl;
            self.timer_mmio_dirty = false;
        }
        let _ = self
            .graph
            .sync_guest_timer(state.timer.counter, state.timer.ctl, state.timer.cval);
        // Non-timer graph sources enter the architectural external-interrupt
        // pending state at the same committed-instruction boundary.  The
        // timer has its own CNTP path in GuestCpuState; omitting it here
        // avoids delivering one physical condition twice.
        if self.graph.aic.take_non_timer(state.affinity).is_some() {
            state.smp.route_external(1u64 << state.affinity);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn graph_is_m1_only_and_reset_is_synchronous() {
        let mut graph = M1MachineGraph::new(0x20_000);
        assert!(graph.valid());
        assert!(!graph.runtime_active);
        assert_eq!(graph.identity.soc_id, M1_SOC_T8103);
        assert_eq!(graph.identity.cpu_count, M1_CPU_COUNT);
        assert!(graph.device_ready(M1DeviceKind::Aic));
        assert!(graph.device_ready(M1DeviceKind::Dart));
        let generation = graph.reset_generation;
        graph.timer.counter = 99;
        graph.display.frame_count = 2;
        graph.reset();
        assert!(graph.reset_generation > generation);
        assert_eq!(graph.timer.counter, 0);
        assert_eq!(graph.display.frame_count, 0);
        assert!(!graph.handoff.prepared);
        assert!(!graph.runtime_active);
    }

    #[test]
    fn runtime_activation_wires_contract_sources_to_cpu_zero() {
        let mut graph = M1MachineGraph::new(0x20_000);
        assert!(graph.activate_runtime());
        assert!(graph.runtime_active);
        assert_eq!(graph.aic.targets[TIMER_SOURCE as usize], 1);
        assert_eq!(graph.aic.targets[STORAGE_SOURCE as usize], 1);
        assert_eq!(graph.aic.targets[DISPLAY_SOURCE as usize], 1);
        assert_eq!(graph.aic.targets[RECOVERY_SOURCE as usize], 1);
        assert_eq!(graph.take_interrupt(0), None);
        assert!(graph.sync_guest_timer(3, 0, 0));
        assert_eq!(graph.timer.counter, 3);
        assert_eq!(graph.take_interrupt(0), None);
        assert!(graph.sync_guest_timer(4, 1, 4));
        assert_eq!(graph.take_interrupt(0), Some(TIMER_SOURCE));
    }

    #[test]
    fn dart_mapping_executes_bounded_dma_and_invalidates() {
        let mut graph = M1MachineGraph::new(0x4000);
        let mut guest = [0u8; 0x4000];
        guest[0..4].copy_from_slice(b"M1!!");
        assert_eq!(
            graph.map_dma(
                7,
                0x10_000,
                0,
                M1_DART_GRANULE,
                M1DmaAccess::Bidirectional
            ),
            Ok(())
        );
        let mut destination = [0u8; 4];
        assert_eq!(
            graph.dma_read(7, 0x10_000, &mut destination, &guest),
            Ok(())
        );
        assert_eq!(&destination, b"M1!!");
        assert_eq!(graph.dma_write(7, 0x10_004, b"DMA!", &mut guest), Ok(()));
        assert_eq!(&guest[4..8], b"DMA!");
        assert_eq!(
            graph.map_dma(7, 0x10_000, 0x1000, M1_DART_GRANULE, M1DmaAccess::DeviceReadGuest),
            Err(M1DmaFault::Overlap)
        );
        assert!(graph.unmap_dma(7, 0x10_000, M1_DART_GRANULE));
        assert_eq!(
            graph.dma_read(7, 0x10_000, &mut destination, &guest),
            Err(M1DmaFault::Unmapped)
        );
    }

    #[test]
    fn dart_permissions_and_ram_bounds_are_distinct() {
        let mut graph = M1MachineGraph::new(0x2000);
        assert_eq!(
            graph.map_dma(1, 0x4000, 0x1000, M1_DART_GRANULE, M1DmaAccess::DeviceReadGuest),
            Ok(())
        );
        let mut ram = [0u8; 0x2000];
        let mut out = [0u8; 4];
        assert_eq!(
            graph.dma_write(1, 0x4000, b"nope", &mut ram),
            Err(M1DmaFault::Permission)
        );
        assert_eq!(
            graph.dma_read(1, 0x5000, &mut out, &ram),
            Err(M1DmaFault::Unmapped)
        );
        assert_eq!(
            graph.map_dma(2, 0x8000, 0x1000, 0x2000, M1DmaAccess::Bidirectional),
            Err(M1DmaFault::InvalidArguments)
        );
    }

    #[test]
    fn timer_is_routed_through_aic_and_acknowledged() {
        let mut graph = M1MachineGraph::new(0x4000);
        assert!(graph.route_interrupt(TIMER_SOURCE, 1 << 3));
        graph.program_timer(10, true, false);
        graph.tick(9);
        assert_eq!(graph.take_interrupt(3), None);
        graph.tick(1);
        assert_eq!(graph.take_interrupt(3), Some(TIMER_SOURCE));
        assert_eq!(graph.take_interrupt(0), None);
        assert!(graph.acknowledge_interrupt(TIMER_SOURCE));
        assert_eq!(graph.take_interrupt(3), None);
    }

    #[test]
    fn display_contract_has_mmio_and_present_irq() {
        let mut graph = M1MachineGraph::new(0x4000);
        assert_eq!(graph.present_display(), Err(M1DisplayFault::NotConfigured));
        assert_eq!(
            graph.configure_display(0x1000, 1920 * 4 * 2, 1920, 2, 1920 * 4, M1DisplayFormat::Xrgb8888),
            Ok(())
        );
        assert_eq!(graph.display_mmio_read(0x04, 4), Some(1920));
        assert_eq!(graph.display_mmio_write(0, 4, 1), Ok(()));
        assert_eq!(graph.display_mmio_read(0, 4), Some(0b111));
        assert_eq!(graph.take_interrupt(0), Some(DISPLAY_SOURCE));
    }

    #[test]
    fn recovery_envelope_checks_length_crc_sequence_and_keeps_signature_unknown() {
        let payload = b"opaque-27-recovery-input";
        let mut frame = [0u8; M1_RECOVERY_HEADER_BYTES + 64];
        let length = M1RecoveryTransport::encode(0, 3, payload, &mut frame).unwrap();
        let mut graph = M1MachineGraph::new(0x4000);
        assert_eq!(graph.ingest_recovery(&frame[..length]), Ok(payload.len()));
        assert_eq!(graph.recovery_payload(), payload);
        assert!(!graph.recovery.signature_verified);
        assert_eq!(graph.take_interrupt(0), Some(RECOVERY_SOURCE));
        assert_eq!(graph.ingest_recovery(&frame[..length]), Err(M1RecoveryFault::Sequence));
        frame[length - 1] ^= 1;
        assert_eq!(graph.ingest_recovery(&frame[..length]), Err(M1RecoveryFault::BadChecksum));
    }

    #[test]
    fn storage_backend_is_caller_owned_and_bounded() {
        let mut graph = M1MachineGraph::new(0x4000);
        assert!(graph.attach_storage(2, false));
        let mut backend = [0u8; M1_STORAGE_BLOCK_BYTES * 2];
        let source = [0x5au8; M1_STORAGE_BLOCK_BYTES];
        assert_eq!(graph.storage.write(1, &source, &mut backend), Ok(()));
        let mut destination = [0u8; M1_STORAGE_BLOCK_BYTES];
        assert_eq!(graph.storage.read(1, &backend, &mut destination), Ok(()));
        assert_eq!(destination, source);
        graph.storage.read_only = true;
        assert_eq!(
            graph.storage.write(0, &source, &mut backend),
            Err(M1StorageFault::ReadOnly)
        );
    }

    #[test]
    fn firmware_handoff_requires_in_ram_aligned_metadata() {
        let mut graph = M1MachineGraph::new(0x4000);
        assert!(graph.configure_handoff(0x100, 0x2000, 0x100));
        assert!(graph.handoff.prepared);
        assert!(!graph.handoff.signature_verified);
        assert!(!graph.configure_handoff(0x101, 0x2000, 0x100));
        assert!(!graph.configure_handoff(0x100, 0x3ff8, 0x100));
    }

    #[test]
    fn logical_mmio_dispatch_covers_every_m1_graph_device() {
        let mut graph = M1MachineGraph::new(0x20_000);
        assert_eq!(graph.mmio_read(M1_LOGICAL_FIRMWARE_BASE, 32), Ok(u64::from(M1_SOC_T8103)));
        assert_eq!(graph.mmio_read(M1_LOGICAL_AIC_BASE + 0x08, 64), Ok(u64::MAX));
        assert_eq!(graph.mmio_read(M1_LOGICAL_TIMER_BASE + 0x18, 64), Ok(M1_COUNTER_FREQUENCY));
        assert_eq!(graph.mmio_read(M1_LOGICAL_DART_BASE, 32), Ok(0));
        assert_eq!(graph.mmio_read(M1_LOGICAL_STORAGE_BASE, 64), Ok(0));
        assert_eq!(graph.mmio_read(M1_LOGICAL_RECOVERY_BASE, 32), Ok(0));
        assert_eq!(graph.mmio_read(M1_LOGICAL_DISPLAY_BASE, 32), Ok(0));
        assert_eq!(graph.mmio_read(M1_LOGICAL_UART_BASE + 0x04, 32), Ok(1));

        assert_eq!(
            graph.configure_display(0x1000, 16 * 4, 4, 4, 16, M1DisplayFormat::Xrgb8888),
            Ok(())
        );
        assert_eq!(graph.mmio_write(M1_LOGICAL_DISPLAY_BASE, 32, 1), Ok(()));
        assert_eq!(graph.mmio_read(M1_LOGICAL_DISPLAY_BASE, 32), Ok(0b111));
        assert_eq!(graph.mmio_write(M1_LOGICAL_UART_BASE, 32, 0x41), Ok(()));
        assert_eq!(graph.mmio_read(M1_LOGICAL_UART_BASE, 32), Ok(0x41));
    }

    #[test]
    fn logical_mmio_connects_timer_and_aic_semantics() {
        let mut graph = M1MachineGraph::new(0x20_000);
        assert!(graph.activate_runtime());
        assert_eq!(graph.mmio_write(M1_LOGICAL_TIMER_BASE + 0x08, 64, 7), Ok(()));
        assert_eq!(graph.mmio_write(M1_LOGICAL_TIMER_BASE + 0x10, 32, 1), Ok(()));
        graph.tick(7);
        assert_eq!(graph.mmio_read(M1_LOGICAL_AIC_BASE, 64), Ok(1));
        assert_eq!(graph.mmio_write(M1_LOGICAL_AIC_BASE + 0x10, 32, TIMER_SOURCE as u64), Ok(()));
        assert_eq!(graph.mmio_read(M1_LOGICAL_AIC_BASE, 64), Ok(0));
    }

    #[test]
    fn logical_mmio_is_bounded_and_fail_closed() {
        let mut graph = M1MachineGraph::new(0x20_000);
        assert_eq!(graph.mmio_read(0x8000, 32), Err(M1MmioFault::Unmapped));
        assert_eq!(graph.mmio_read(M1_LOGICAL_TIMER_BASE, 16), Err(M1MmioFault::InvalidWidth));
        assert_eq!(graph.mmio_read(M1_LOGICAL_TIMER_BASE + 0xfff, 32), Err(M1MmioFault::OutOfRange));
        assert_eq!(graph.mmio_write(M1_LOGICAL_FIRMWARE_BASE, 32, 1), Err(M1MmioFault::ReadOnly));
        assert_eq!(graph.mmio_write(M1_LOGICAL_DISPLAY_BASE + 0x04, 32, 1), Err(M1MmioFault::InvalidRegister));
        assert_eq!(graph.mmio_write(M1_LOGICAL_UART_BASE, 32, 0x100), Err(M1MmioFault::InvalidRegister));
        assert_eq!(graph.mmio_write(M1_LOGICAL_AIC_BASE + 0x08, 64, 1 << M1_INTERRUPT_SOURCES), Err(M1MmioFault::InvalidRegister));
        assert_eq!(graph.mmio_write(M1_LOGICAL_AIC_BASE + 0x18, 64, 0), Err(M1MmioFault::InvalidRegister));
        assert_eq!(graph.mmio_write(M1_LOGICAL_AIC_BASE + 0x18, 64, (1 << 8) | (1 << (8 + M1_CPU_COUNT))), Err(M1MmioFault::InvalidRegister));
    }
}
