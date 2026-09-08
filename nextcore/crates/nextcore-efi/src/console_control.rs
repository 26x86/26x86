//! Optional EFI console service. See the public BP20-J contract artifact.
//! No Boot Services table replacement or child-specific behavior is used.
use alloc::{boxed::Box, format};
use core::{
    ffi::c_void,
    fmt,
    fmt::Write,
    ptr,
    sync::atomic::{AtomicBool, AtomicUsize, Ordering},
};
use uefi::{guid, table, Status};
use uefi_raw::protocol::console::serial::SerialIoProtocol;
use uefi_raw::protocol::console::{GraphicsOutputProtocol, SimpleTextOutputProtocol};
use uefi_raw::table::boot::{BootServices, InterfaceType};
use uefi_raw::{Boolean, Guid, Handle};

pub const GUID: Guid = guid!("f42f7782-012e-4c12-9956-49f94304f721");
const UGA_GUID: Guid = guid!("982c298b-f4fa-41cb-b838-77aa688fb839");
pub const TEXT: u32 = 0;
pub const GRAPHICS: u32 = 1;

/// Intel's three-function public layout. Integer modes reject invalid values
/// without constructing a Rust enum from firmware-controlled input.
#[repr(C)]
pub struct Interface {
    pub get_mode:
        unsafe extern "efiapi" fn(*mut Interface, *mut u32, *mut Boolean, *mut Boolean) -> Status,
    pub set_mode: unsafe extern "efiapi" fn(*mut Interface, u32) -> Status,
    pub lock_stdin: unsafe extern "efiapi" fn(*mut Interface, *const u16) -> Status,
}

#[repr(C)]
struct Provider {
    interface: Interface,
    services: *mut BootServices,
    output: *mut SimpleTextOutputProtocol,
    serial: *mut SerialIoProtocol,
    logging: AtomicBool,
    events: AtomicUsize,
}

/// Storage and the containing EFI image must outlive the published callbacks.
/// Drop enforces removal and cannot return into an image unload on failure.
#[must_use]
pub struct Lease {
    owned: Option<(Handle, Box<Provider>)>,
    interface: *mut Interface,
    report: fn(&str),
}

impl Lease {
    pub fn acquire(report: fn(&str)) -> Result<Self, Status> {
        let system = table::system_table_raw().ok_or(Status::NOT_READY)?;
        // SAFETY: entry initialized this live firmware table. No reference to
        // it or to a firmware protocol is held across child execution.
        let services = unsafe { (*system.as_ptr()).boot_services };
        if services.is_null() {
            return Err(Status::NOT_READY);
        }
        let existing = unsafe { locate(services, &GUID)? };
        if let Some(interface) = existing {
            report("NEXTCORE: CONSOLE_REUSED");
            return Ok(Self {
                owned: None,
                interface: interface.cast(),
                report,
            });
        }
        let mut provider = Box::new(Provider {
            interface: Interface {
                get_mode,
                set_mode,
                lock_stdin,
            },
            services,
            output: unsafe { (*system.as_ptr()).stdout },
            serial: unsafe {
                locate(services, &SerialIoProtocol::GUID)
                    .ok()
                    .flatten()
                    .unwrap_or(ptr::null_mut())
                    .cast()
            },
            logging: AtomicBool::new(false),
            events: AtomicUsize::new(0),
        });
        let (index, columns, rows) = unsafe { provider.text_state()? };
        let graphics = unsafe { provider.graphics_exists()? };
        let interface = ptr::addr_of_mut!(provider.interface);
        let mut handle = ptr::null_mut();
        // SAFETY: Box stabilizes both interface and its containing context.
        // The lease owns it until exact successful uninstall.
        let status = unsafe {
            ((*services).install_protocol_interface)(
                &mut handle,
                &GUID,
                InterfaceType::NATIVE_INTERFACE,
                interface.cast(),
            )
        };
        if status != Status::SUCCESS {
            return Err(status);
        }
        let lease = Self {
            owned: Some((handle, provider)),
            interface,
            report,
        };
        if unsafe { locate(services, &GUID)? } != Some(interface.cast()) {
            // Drop also protects the parent code lifetime if uninstall fails.
            drop(lease);
            return Err(Status::DEVICE_ERROR);
        }
        report(&format!("NEXTCORE: CONSOLE_INSTALLED text_mode={index} columns={columns} rows={rows} system_graphics={graphics}"));
        Ok(lease)
    }

    #[cfg(feature = "console-probe")]
    #[allow(dead_code)] // Also compiled into BOOTX64 when the probe feature is set.
    pub fn interface(&self) -> *mut Interface {
        self.interface
    }

    #[cfg(feature = "console-probe")]
    #[allow(dead_code)] // Probe-only inspection of ownership; no production caller.
    pub fn is_owned(&self) -> bool {
        self.owned.is_some()
    }

    /// Must be called while Boot Services are live, after the child returns.
    /// A failed removal deliberately does not return/unload published code.
    pub fn release(self) {
        drop(self);
    }
}

impl Drop for Lease {
    fn drop(&mut self) {
        let Some((handle, provider)) = self.owned.as_ref() else {
            (self.report)("NEXTCORE: CONSOLE_RELEASE reused=true removed=false");
            return;
        };
        // SAFETY: only this lease removes its exact registered pair, and all
        // child calls have returned before release. Storage is still owned.
        let status = unsafe {
            ((*provider.services).uninstall_protocol_interface)(
                *handle,
                &GUID,
                self.interface.cast(),
            )
        };
        (self.report)(&format!("NEXTCORE: CONSOLE_UNINSTALL status={status:?}"));
        if status != Status::SUCCESS {
            (self.report)("NEXTCORE: CONSOLE_RETAINED reason=UNINSTALL_FAILED image_resident=true");
            // Leaking data alone would be insufficient: callbacks reside in
            // this EFI image. Stay resident instead of returning to its loader.
            loop {
                core::hint::spin_loop();
            }
        }
        self.owned.take();
        (self.report)("NEXTCORE: CONSOLE_RELEASE reused=false removed=true storage_freed=true");
    }
}

unsafe fn locate(services: *mut BootServices, guid: &Guid) -> Result<Option<*mut c_void>, Status> {
    let mut found = ptr::null_mut();
    let status = ((*services).locate_protocol)(guid, ptr::null_mut(), &mut found);
    classify_lookup(status, found)
}

/// Protocol existence does not imply initialized/linear-framebuffer metadata.
pub(crate) fn classify_lookup(
    status: Status,
    found: *mut c_void,
) -> Result<Option<*mut c_void>, Status> {
    match status {
        Status::SUCCESS if !found.is_null() => Ok(Some(found)),
        Status::SUCCESS => Err(Status::DEVICE_ERROR),
        Status::NOT_FOUND => Ok(None),
        other => Err(other),
    }
}

impl Provider {
    unsafe fn text_state(&self) -> Result<(usize, usize, usize), Status> {
        if self.output.is_null() || (*self.output).mode.is_null() {
            return Err(Status::NOT_READY);
        }
        let mode = &*(*self.output).mode;
        if mode.mode < 0 || mode.mode >= mode.max_mode {
            return Err(Status::NOT_READY);
        }
        let index = mode.mode as usize;
        let (mut columns, mut rows) = (0, 0);
        let status = ((*self.output).query_mode)(self.output, index, &mut columns, &mut rows);
        if status != Status::SUCCESS {
            return Err(status);
        }
        if columns == 0 || rows == 0 {
            return Err(Status::NOT_READY);
        }
        Ok((index, columns, rows))
    }

    unsafe fn graphics_exists(&self) -> Result<bool, Status> {
        if locate(self.services, &GraphicsOutputProtocol::GUID)?.is_some() {
            return Ok(true);
        }
        Ok(locate(self.services, &UGA_GUID)?.is_some())
    }

    /// Fixed-size, allocation-free telemetry. Logging failures do not alter a
    /// callback result, and nested logging cannot recursively issue writes.
    unsafe fn event(&self, args: fmt::Arguments<'_>) {
        if self.serial.is_null()
            || self.events.fetch_add(1, Ordering::Relaxed) >= 64
            || self.logging.swap(true, Ordering::AcqRel)
        {
            return;
        }
        struct Buffer {
            bytes: [u8; 256],
            count: usize,
        }
        impl Write for Buffer {
            fn write_str(&mut self, value: &str) -> fmt::Result {
                let end = self.count.checked_add(value.len()).ok_or(fmt::Error)?;
                self.bytes
                    .get_mut(self.count..end)
                    .ok_or(fmt::Error)?
                    .copy_from_slice(value.as_bytes());
                self.count = end;
                Ok(())
            }
        }
        let mut line = Buffer {
            bytes: [0; 256],
            count: 0,
        };
        if line.write_fmt(args).is_ok() && line.write_str("\r\n").is_ok() {
            let _ = ((*self.serial).write)(self.serial, &mut line.count, line.bytes.as_ptr());
        }
        self.logging.store(false, Ordering::Release);
    }
}

unsafe fn context<'a>(this: *mut Interface) -> Result<&'a Provider, Status> {
    if this.is_null() {
        return Err(Status::INVALID_PARAMETER);
    }
    // Public EFI callers must pass the live interface returned by lookup.
    // repr(C) puts that interface at offset zero of its stable context.
    Ok(&*this.cast::<Provider>())
}

unsafe extern "efiapi" fn get_mode(
    this: *mut Interface,
    mode: *mut u32,
    graphics: *mut Boolean,
    locked: *mut Boolean,
) -> Status {
    let provider = match context(this) {
        Ok(p) => p,
        Err(e) => return e,
    };
    let result = provider
        .text_state()
        .and_then(|_| provider.graphics_exists());
    let status = match result {
        Ok(exists) => {
            if !mode.is_null() {
                *mode = TEXT;
            }
            if !graphics.is_null() {
                *graphics = Boolean(u8::from(exists));
            }
            if !locked.is_null() {
                *locked = Boolean(0);
            }
            Status::SUCCESS
        }
        Err(error) => error,
    };
    provider.event(format_args!(
        "NEXTCORE: CONSOLE_GET_MODE status={status:?} system_graphics={result:?}"
    ));
    status
}

unsafe extern "efiapi" fn set_mode(this: *mut Interface, mode: u32) -> Status {
    let provider = match context(this) {
        Ok(p) => p,
        Err(e) => return e,
    };
    let status = match mode {
        TEXT => match provider.text_state() {
            Ok((index, _, _)) => ((*provider.output).set_mode)(provider.output, index),
            Err(e) => e,
        },
        GRAPHICS => Status::UNSUPPORTED,
        _ => Status::INVALID_PARAMETER,
    };
    provider.event(format_args!(
        "NEXTCORE: CONSOLE_SET_MODE mode={mode} status={status:?}"
    ));
    status
}

unsafe extern "efiapi" fn lock_stdin(this: *mut Interface, password: *const u16) -> Status {
    let provider = match context(this) {
        Ok(p) => p,
        Err(e) => return e,
    };
    let status = if password.is_null() {
        Status::SUCCESS
    } else {
        Status::DEVICE_ERROR
    };
    provider.event(format_args!(
        "NEXTCORE: CONSOLE_LOCK_STDIN lock={} status={status:?}",
        !password.is_null()
    ));
    status
}
