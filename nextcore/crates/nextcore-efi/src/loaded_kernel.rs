//! UEFI ownership of one explicitly placed Mach-O image and a trailing arena.
//!
//! Physical placement and the entry ABI belong to the caller's profile. This
//! module does not infer a VA-to-PA mapping, relocate an image, set page-table
//! protections, call ExitBootServices, or execute the entry point.
//!
//! Allocation uses UEFI 2.10A 7.2.1 AllocatePages/AllocateAddress and 7.2.2
//! FreePages: <https://uefi.org/specs/UEFI/2.10_A/07_Services_Boot_Services.html>.
//! The initial copy is checked with volatile reads; this is readback of allocated
//! RAM, not proof of storage persistence or kernel execution.

use core::{ptr::NonNull, slice};
use nextcore_core::macho_image::{parse_macho_image, MachOImagePlan, MAX_IMAGE_SIZE, PAGE_SIZE};
use uefi::{
    boot::{self, AllocateType},
    mem::memory_map::MemoryType,
    Status,
};

const FOUR_GIB: u64 = 1 << 32;
const MAX_EXTRA_PAGES: usize = 256;

/// Owns an initialized, contiguous allocation while UEFI boot services exist.
///
/// Drop releases all pages, including the arena. Before a successful
/// ExitBootServices transition, the caller must put this owner in
/// `core::mem::ManuallyDrop` or use `core::mem::forget` so its boot-service
/// destructor cannot run afterward. On an aborted transition, release the
/// owner while boot services remain available. Do not free these pages through
/// another API while this owner or any borrowed arena slice is alive.
pub struct LoadedKernel {
    allocation: NonNull<u8>,
    pages: usize,
    image_size: usize,
    arena_size: usize,
    entry_offset: usize,
}

impl LoadedKernel {
    /// Allocate exactly at `physical_base`, zero the entire allocation, copy the
    /// validated segment ranges, and verify copied bytes, zero-fill, and holes.
    ///
    /// `plan` must exactly match `parse_macho_image(source)`. Re-parsing before
    /// allocation rejects forged public plan fields and a plan from a different
    /// source layout; it also re-establishes all file/entry/segment bounds.
    /// This does not authenticate the source or establish its required CPU ABI.
    ///
    /// All occupied physical bytes must be below 4 GiB. The optional tail is at
    /// most 256 pages. Physical and image allocation boundaries are page aligned.
    /// Invalid inputs fail before allocation; an allocation or readback failure
    /// returns a UEFI status and releases any pages already acquired.
    pub fn load_at(
        plan: &MachOImagePlan,
        source: &[u8],
        physical_base: u64,
        extra_pages: usize,
    ) -> Result<Self, Status> {
        if physical_base == 0
            || physical_base % PAGE_SIZE != 0
            || plan.image_size == 0
            || plan.image_size > MAX_IMAGE_SIZE
            || plan.image_size % PAGE_SIZE != 0
            || extra_pages > MAX_EXTRA_PAGES
        {
            return Err(Status::INVALID_PARAMETER);
        }
        let arena_size = extra_pages
            .checked_mul(PAGE_SIZE as usize)
            .ok_or(Status::INVALID_PARAMETER)?;
        let total_size = plan
            .image_size
            .checked_add(arena_size as u64)
            .ok_or(Status::INVALID_PARAMETER)?;
        let physical_end = physical_base
            .checked_add(total_size)
            .ok_or(Status::INVALID_PARAMETER)?;
        if physical_end > FOUR_GIB || total_size > isize::MAX as u64 {
            return Err(Status::INVALID_PARAMETER);
        }
        let image_size = usize::try_from(plan.image_size).map_err(|_| Status::INVALID_PARAMETER)?;
        let total_size = usize::try_from(total_size).map_err(|_| Status::INVALID_PARAMETER)?;
        let entry_offset =
            usize::try_from(plan.entry_offset).map_err(|_| Status::INVALID_PARAMETER)?;
        if entry_offset >= image_size {
            return Err(Status::INVALID_PARAMETER);
        }
        let validated = parse_macho_image(source).map_err(|_| Status::INVALID_PARAMETER)?;
        if &validated != plan {
            return Err(Status::INVALID_PARAMETER);
        }
        // Do not retain the parser's temporary heap allocation across any
        // firmware memory-map/ExitBootServices work done by the caller later.
        drop(validated);

        // A conforming allocator cannot allocate over the live source, but
        // reject that request explicitly before any destination is written.
        let source_start = source.as_ptr() as usize as u64;
        let source_end = source_start
            .checked_add(source.len() as u64)
            .ok_or(Status::INVALID_PARAMETER)?;
        if physical_base < source_end && source_start < physical_end {
            return Err(Status::INVALID_PARAMETER);
        }

        let pages = total_size / PAGE_SIZE as usize;
        let allocation = boot::allocate_pages(
            AllocateType::Address(physical_base),
            MemoryType::LOADER_CODE,
            pages,
        )
        .map_err(|error| error.status())?;
        // Establish ownership immediately: all later errors trigger FreePages.
        let mut loaded = Self {
            allocation,
            pages,
            image_size,
            arena_size,
            entry_offset,
        };
        if loaded.physical_base() != physical_base {
            return Err(Status::DEVICE_ERROR);
        }
        // SAFETY: AllocatePages returned exclusive ownership of this contiguous
        // range. Initialize every byte before making any Rust slice references.
        unsafe { loaded.allocation.as_ptr().write_bytes(0, total_size) };
        let memory = loaded.all_bytes_mut();
        for segment in &plan.segments {
            // The exact parsed plan guarantees these ranges are within the
            // source/image and that no segment destinations overlap.
            let start = segment.memory_offset as usize;
            let file_end = segment.file_offset + segment.file_size;
            memory[start..start + segment.file_size]
                .copy_from_slice(&source[segment.file_offset..file_end]);
        }

        // Verify each byte once after copying: gaps, payloads, zero-fill tails,
        // the page-rounded image tail, and the complete extra arena.
        let mut previous_end = 0;
        for segment in &plan.segments {
            let start = segment.memory_offset as usize;
            let copied_end = start + segment.file_size;
            let memory_end = start + segment.memory_size as usize;
            let file_end = segment.file_offset + segment.file_size;
            if !verify_memory(&memory[previous_end..start], None)
                || !verify_memory(
                    &memory[start..copied_end],
                    Some(&source[segment.file_offset..file_end]),
                )
                || !verify_memory(&memory[copied_end..memory_end], None)
            {
                return Err(Status::DEVICE_ERROR);
            }
            previous_end = memory_end;
        }
        if !verify_memory(&memory[previous_end..], None) {
            return Err(Status::DEVICE_ERROR);
        }
        Ok(loaded)
    }

    pub fn physical_base(&self) -> u64 {
        self.allocation.as_ptr() as usize as u64
    }

    /// Physical byte corresponding to the parsed entry offset. This is an
    /// address value only; calling it requires a separately established ABI.
    pub fn physical_entry(&self) -> u64 {
        self.physical_base() + self.entry_offset as u64
    }

    pub fn image_size(&self) -> u64 {
        self.image_size as u64
    }

    /// Bytes in the tail after the image, excluding the image itself.
    pub fn arena_size(&self) -> usize {
        self.arena_size
    }

    /// The extra tail, initially all zero, at physical_base() + image_size().
    /// The borrow cannot outlive the page owner. Writes here do not modify the
    /// loaded image; the caller owns validation of its eventual handoff data.
    pub fn arena_bytes_mut(&mut self) -> &mut [u8] {
        let image_size = self.image_size;
        &mut self.all_bytes_mut()[image_size..]
    }

    fn all_bytes_mut(&mut self) -> &mut [u8] {
        // SAFETY: This owner's pages are contiguous, exclusive, and fully
        // initialized before this helper is first called. The length was
        // checked against isize::MAX and the complete physical allocation.
        unsafe {
            slice::from_raw_parts_mut(self.allocation.as_ptr(), self.image_size + self.arena_size)
        }
    }
}

impl Drop for LoadedKernel {
    fn drop(&mut self) {
        // SAFETY: This owner does not expose a mutable allocation pointer and
        // borrows cannot survive Drop. The caller must suppress Drop before
        // ExitBootServices, as required by this type's lifecycle contract.
        // A firmware FreePages failure cannot be propagated from a destructor.
        let _ = unsafe { boot::free_pages(self.allocation, self.pages) };
    }
}

/// Read every destination byte through volatile accesses. Aligned words avoid
/// a byte-at-a-time loop over large zero-filled segments; prefix/suffix bytes
/// keep non-page-aligned Mach-O segment offsets valid.
fn verify_memory(actual: &[u8], expected: Option<&[u8]>) -> bool {
    if expected.is_some_and(|bytes| bytes.len() != actual.len()) {
        return false;
    }
    // SAFETY: u64 has no invalid bit patterns, and actual is initialized RAM.
    let (prefix, words, suffix) = unsafe { actual.align_to::<u64>() };
    let mut offset = 0;
    for byte in prefix {
        // SAFETY: byte is a live, initialized byte within the owned allocation.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |bytes| bytes[offset]) {
            return false;
        }
        offset += 1;
    }
    for word in words {
        let value = expected.map_or(0, |bytes| {
            u64::from_ne_bytes(bytes[offset..offset + 8].try_into().unwrap())
        });
        // SAFETY: align_to supplies a valid, aligned u64 within actual.
        if unsafe { core::ptr::read_volatile(word) } != value {
            return false;
        }
        offset += 8;
    }
    for byte in suffix {
        // SAFETY: byte is a live, initialized byte within the owned allocation.
        if unsafe { core::ptr::read_volatile(byte) } != expected.map_or(0, |bytes| bytes[offset]) {
            return false;
        }
        offset += 1;
    }
    true
}
