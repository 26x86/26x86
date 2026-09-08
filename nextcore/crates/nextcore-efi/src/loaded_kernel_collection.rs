//! Owned UEFI LoaderData pages for read-only KC staging, never execution.
//! See artifacts/kc-efi-staging-contract-20260908.md and UEFI 2.10A section 7.2.
use alloc::{format, vec::Vec};
use core::{mem::size_of, ptr::NonNull, slice};
use nextcore_core::kc_staging::{
    KcStagingError, KcStagingPlan, StagingVerification, STAGING_PAGE_SIZE,
};
use uefi::{
    boot::{self, AllocateType, MemoryDescriptor, MemoryType},
    table, Status,
};

const FOUR_GIB: u64 = 1 << 32;
const MAP_BYTES: usize = 128 * 1024;
const MAX_DESCRIPTORS: usize = 4096;
type Result<T> = core::result::Result<T, Status>;

/// A bounded initialized buffer. No allocation occurs in refresh/coverage.
struct MapBuffer {
    words: Vec<u64>,
    bytes: usize,
    stride: usize,
}
impl MapBuffer {
    fn new() -> Result<Self> {
        let mut words = Vec::new();
        words
            .try_reserve_exact(MAP_BYTES / 8)
            .map_err(|_| Status::OUT_OF_RESOURCES)?;
        words.resize(MAP_BYTES / 8, 0);
        Ok(Self {
            words,
            bytes: 0,
            stride: 0,
        })
    }
    fn refresh(&mut self) -> Result<()> {
        let system = table::system_table_raw().ok_or(Status::NOT_READY)?;
        // SAFETY: The entry installed the live UEFI table. This module never
        // exits Boot Services; its owner must be released before such a call.
        let services = unsafe { (*system.as_ptr()).boot_services };
        if services.is_null() {
            return Err(Status::NOT_READY);
        }
        let get_map = unsafe { (*services).get_memory_map };
        let (mut bytes, mut key, mut stride, mut version) = (MAP_BYTES, 0, 0, 0);
        // SAFETY: aligned, writable, initialized buffer and valid output slots.
        let status = unsafe {
            get_map(
                &mut bytes,
                self.words.as_mut_ptr().cast(),
                &mut key,
                &mut stride,
                &mut version,
            )
        };
        if status != Status::SUCCESS {
            return Err(status);
        }
        if version != 1
            || stride < size_of::<MemoryDescriptor>()
            || bytes > MAP_BYTES
            || bytes == 0
            || bytes % stride != 0
            || bytes / stride > MAX_DESCRIPTORS
        {
            return Err(Status::COMPROMISED_DATA);
        }
        self.bytes = bytes;
        self.stride = stride;
        Ok(())
    }
    fn entry(&self, index: usize) -> MemoryDescriptor {
        // SAFETY: refresh bounded count and stride. Read the ABI prefix without
        // assuming that future descriptor strides share Rust alignment.
        unsafe {
            self.words
                .as_ptr()
                .cast::<u8>()
                .add(index * self.stride)
                .cast::<MemoryDescriptor>()
                .read_unaligned()
        }
    }
    fn coverage(&self, base: u64, bytes: usize, expected: MemoryType) -> Result<usize> {
        let end = base
            .checked_add(bytes as u64)
            .ok_or(Status::COMPROMISED_DATA)?;
        let mut total = 0u64;
        let mut intersecting = 0;
        for index in 0..self.bytes / self.stride {
            let d = self.entry(index);
            let length = d
                .page_count
                .checked_mul(STAGING_PAGE_SIZE)
                .ok_or(Status::COMPROMISED_DATA)?;
            let limit = d
                .phys_start
                .checked_add(length)
                .ok_or(Status::COMPROMISED_DATA)?;
            if d.phys_start % STAGING_PAGE_SIZE != 0 {
                return Err(Status::COMPROMISED_DATA);
            }
            let lo = base.max(d.phys_start);
            let hi = end.min(limit);
            if lo < hi {
                if d.ty != expected {
                    return Err(Status::COMPROMISED_DATA);
                }
                total = total.checked_add(hi - lo).ok_or(Status::COMPROMISED_DATA)?;
                intersecting += 1;
            }
        }
        // Sum equality rejects overlap after the gap-free traversal below.
        if total != bytes as u64 {
            return Err(Status::COMPROMISED_DATA);
        }
        let mut cursor = base;
        for _ in 0..intersecting {
            if cursor == end {
                return Ok(intersecting);
            }
            let mut next = cursor;
            for index in 0..self.bytes / self.stride {
                let d = self.entry(index);
                let limit = d.phys_start + d.page_count * STAGING_PAGE_SIZE;
                if d.phys_start <= cursor && cursor < limit {
                    next = next.max(limit.min(end));
                }
            }
            if next == cursor {
                return Err(Status::COMPROMISED_DATA);
            }
            cursor = next;
        }
        if cursor == end {
            Ok(intersecting)
        } else {
            Err(Status::COMPROMISED_DATA)
        }
    }
}

struct Pages {
    pointer: Option<NonNull<u8>>,
    count: usize,
    bytes: usize,
    map: MapBuffer,
    report: fn(&str),
}
impl Pages {
    fn new(bytes: usize, report: fn(&str)) -> Result<Self> {
        if bytes == 0 || bytes % STAGING_PAGE_SIZE as usize != 0 || bytes > isize::MAX as usize {
            return Err(Status::INVALID_PARAMETER);
        }
        let map = MapBuffer::new()?;
        let count = bytes / STAGING_PAGE_SIZE as usize;
        let pointer = boot::allocate_pages(
            AllocateType::MaxAddress(FOUR_GIB - 1),
            MemoryType::LOADER_DATA,
            count,
        )
        .map_err(|e| e.status())?;
        // Establish RAII ownership before any subsequent validation can fail.
        let pages = Self {
            pointer: Some(pointer),
            count,
            bytes,
            map,
            report,
        };
        let base = pages.base();
        if base == 0
            || base % STAGING_PAGE_SIZE != 0
            || base
                .checked_add(bytes as u64)
                .is_none_or(|end| end > FOUR_GIB)
        {
            return Err(Status::COMPROMISED_DATA);
        }
        Ok(pages)
    }
    fn base(&self) -> u64 {
        self.pointer.unwrap().as_ptr() as usize as u64
    }
    fn release_inner(&mut self, mode: &str) -> Result<()> {
        let Some(pointer) = self.pointer.take() else {
            return Ok(());
        };
        let base = pointer.as_ptr() as usize as u64;
        // SAFETY: This private owner obtained exactly these pages. No slices
        // survive release. Attempt exactly once, including on firmware error.
        let status = unsafe { boot::free_pages(pointer, self.count) }
            .map_or_else(|e| e.status(), |_| Status::SUCCESS);
        // Observe the map before logs or any heap operation could reuse pages.
        let coverage = if status == Status::SUCCESS {
            self.map.refresh().and_then(|_| {
                self.map
                    .coverage(base, self.bytes, MemoryType::CONVENTIONAL)
            })
        } else {
            Err(status)
        };
        let map_status = coverage.as_ref().map_or_else(|s| *s, |_| Status::SUCCESS);
        (self.report)(&format!("NXKC: RELEASE mode={mode} base={base:#x} pages={} status={status:?} map_status={map_status:?} descriptors={}", self.count, coverage.unwrap_or(0)));
        if status == Status::SUCCESS && map_status == Status::SUCCESS {
            Ok(())
        } else {
            Err(Status::DEVICE_ERROR)
        }
    }
}
impl Drop for Pages {
    fn drop(&mut self) {
        let _ = self.release_inner("drop");
    }
}

/// Owns an initialized allocation only while Boot Services remain active.
/// No execution address, mutable image reference or ownership transfer is
/// exposed. This type must not be retained across ExitBootServices.
pub struct LoadedKernelCollection<'a> {
    pages: Pages,
    plan: KcStagingPlan<'a>,
    verification: StagingVerification,
    map_descriptors: usize,
}
impl<'a> LoadedKernelCollection<'a> {
    pub fn load(source: &'a [u8], report: fn(&str)) -> Result<Self> {
        let plan = KcStagingPlan::new(source).map_err(|_| Status::LOAD_ERROR)?;
        let mut pages = Pages::new(plan.arena_size(), report)?;
        let base = pages.base();
        let source_base = source.as_ptr() as usize as u64;
        let source_end = source_base
            .checked_add(source.len() as u64)
            .ok_or(Status::INVALID_PARAMETER)?;
        if base < source_end && source_base < base + pages.bytes as u64 {
            return Err(Status::INVALID_PARAMETER);
        }
        pages.map.refresh()?;
        let map_descriptors = pages
            .map
            .coverage(base, pages.bytes, MemoryType::LOADER_DATA)?;
        report(&format!("NXKC: ALLOCATED base={base:#x} pages={} bytes={} descriptors={map_descriptors} source_disjoint=true", pages.count, pages.bytes));
        let pointer = pages.pointer.unwrap().as_ptr();
        // SAFETY: exclusive page ownership, checked size and source disjointness.
        // Initialize RAM before creating a Rust slice; stage_into then applies
        // the source-bound outer copy/zero plan and full volatile readback.
        unsafe {
            pointer.write_bytes(0, pages.bytes);
        }
        let destination = unsafe { slice::from_raw_parts_mut(pointer, pages.bytes) };
        let verification = plan
            .stage_into(destination)
            .map_err(|_| Status::COMPROMISED_DATA)?;
        Ok(Self {
            pages,
            plan,
            verification,
            map_descriptors,
        })
    }
    pub fn verification(&self) -> &StagingVerification {
        &self.verification
    }
    pub fn physical_base(&self) -> u64 {
        self.pages.base()
    }
    pub fn map_descriptors(&self) -> usize {
        self.map_descriptors
    }
    pub fn release(mut self) -> Result<()> {
        self.pages.release_inner("explicit")
    }

    /// Explicit diagnostic only. Alter owned destination RAM, require actual
    /// mismatch detection, then let RAII discard and release it. Never source.
    pub fn probe_readback_failure(self) -> Result<()> {
        let pointer = self.pages.pointer.unwrap().as_ptr();
        // SAFETY: the live owner has exclusive initialized RAM and no exposed
        // image references; no instruction from this allocation is executed.
        unsafe {
            pointer.write_volatile(pointer.read_volatile() ^ 0xff);
        }
        let bytes = unsafe { slice::from_raw_parts(pointer, self.pages.bytes) };
        if self.plan.verify(bytes) != Err(KcStagingError::ReadbackMismatch) {
            return Err(Status::DEVICE_ERROR);
        }
        (self.pages.report)("NXKC: READBACK_REJECTION_OK");
        Ok(()) // Pages::drop records the real FreePages result before returning.
    }
}
