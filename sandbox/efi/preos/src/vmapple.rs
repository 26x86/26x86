//! Fixed-size VMApple TCG machine graph.
//!
//! The graph is intentionally independent of QEMU's object model.  QEMU is
//! the software CPU/host harness; this module records and exercises the
//! guest-visible addresses and reset/read/write semantics needed by the
//! portable VMApple launch path.  No physical-M1 identity is inferred from
//! this virtual profile.

#![allow(dead_code)]

pub(crate) const VMAPPLE_FIRMWARE_BASE: u64 = 0x0010_0000;
pub(crate) const VMAPPLE_FIRMWARE_BYTES: u64 = 0x0010_0000;
pub(crate) const VMAPPLE_CONFIG_BASE: u64 = 0x0040_0000;
pub(crate) const VMAPPLE_CONFIG_BYTES: u64 = 0x0001_0000;
// QEMU VMApple's GIC distributor and redistributor windows are contiguous.
// The descriptor keeps them in one bounded range; it does not relabel GIC as
// the native Sandbox AIC.
pub(crate) const VMAPPLE_GIC_BASE: u64 = 0x1000_0000;
pub(crate) const VMAPPLE_GIC_BYTES: u64 = 0x0041_0000;
pub(crate) const VMAPPLE_UART_BASE: u64 = 0x2001_0000;
pub(crate) const VMAPPLE_UART_BYTES: u64 = 0x0001_0000;
pub(crate) const VMAPPLE_RTC_BASE: u64 = 0x2005_0000;
pub(crate) const VMAPPLE_RTC_BYTES: u64 = 0x0000_1000;
pub(crate) const VMAPPLE_GPIO_BASE: u64 = 0x2006_0000;
pub(crate) const VMAPPLE_GPIO_BYTES: u64 = 0x0000_1000;
pub(crate) const VMAPPLE_PVPANIC_BASE: u64 = 0x2007_0000;
pub(crate) const VMAPPLE_PVPANIC_BYTES: u64 = 0x0000_0002;
pub(crate) const VMAPPLE_BDIF_BASE: u64 = 0x3000_0000;
pub(crate) const VMAPPLE_BDIF_BYTES: u64 = 0x0020_0000;
pub(crate) const VMAPPLE_DISPLAY_BASE: u64 = 0x3020_0000;
pub(crate) const VMAPPLE_DISPLAY_BYTES: u64 = 0x0001_0000;
pub(crate) const VMAPPLE_DISPLAY_CONTROL_BASE: u64 = 0x3021_0000;
pub(crate) const VMAPPLE_DISPLAY_CONTROL_BYTES: u64 = 0x0001_0000;
pub(crate) const VMAPPLE_AES_BASE: u64 = 0x3022_0000;
pub(crate) const VMAPPLE_AES_BYTES: u64 = 0x0000_4000;
pub(crate) const VMAPPLE_AES_CONTROL_BASE: u64 = 0x3023_0000;
pub(crate) const VMAPPLE_AES_CONTROL_BYTES: u64 = 0x0000_4000;
pub(crate) const VMAPPLE_PCIE_ECAM_BASE: u64 = 0x4000_0000;
pub(crate) const VMAPPLE_PCIE_ECAM_BYTES: u64 = 0x1000_0000;
pub(crate) const VMAPPLE_PCIE_MMIO_BASE: u64 = 0x5000_0000;
pub(crate) const VMAPPLE_PCIE_MMIO_BYTES: u64 = 0x1fff_0000;
pub(crate) const VMAPPLE_RAM_BASE: u64 = 0x7000_0000;

pub(crate) const VMAPPLE_MAX_CPUS: u32 = 32;
pub(crate) const VMAPPLE_CONFIG_VERSION: u32 = 2;
pub(crate) const UART_FR_TXFE: u32 = 1 << 7;
pub(crate) const UART_FR_RXFE: u32 = 1 << 4;
pub(crate) const GIC_ENABLE: u32 = 1 << 0;
pub(crate) const GIC_PENDING: u32 = 1 << 1;
pub(crate) const BDIF_READY: u32 = 1 << 0;
pub(crate) const DISPLAY_READY: u32 = 1 << 0;

#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub(crate) enum VfVmappleDeviceKind {
    Config = 1,
    Gic = 2,
    Uart = 3,
    Rtc = 4,
    Gpio = 5,
    Pvpanic = 6,
    Storage = 7,
    Display = 8,
    DisplayControl = 9,
    Firmware = 10,
    Aes = 11,
    AesControl = 12,
    PcieEcam = 13,
    PcieMmio = 14,
}

#[derive(Clone, Copy)]
pub(crate) struct VfVmappleDevice {
    pub(crate) kind: VfVmappleDeviceKind,
    pub(crate) base: u64,
    pub(crate) bytes: u64,
}

impl VfVmappleDevice {
    const EMPTY: Self = Self {
        kind: VfVmappleDeviceKind::Config,
        base: 0,
        bytes: 0,
    };

    fn contains(self, address: u64, width: u64) -> bool {
        match (
            self.base.checked_add(self.bytes),
            address.checked_add(width),
        ) {
            (Some(end), Some(access_end)) => {
                self.bytes != 0 && address >= self.base && access_end <= end
            }
            _ => false,
        }
    }
}

/// A bounded, deterministic virtual machine device graph.
pub(crate) struct VfVmappleMachine {
    pub(crate) cpu_count: u32,
    pub(crate) ram_base: u64,
    pub(crate) ram_bytes: u64,
    pub(crate) ecid: u64,
    pub(crate) devices: [VfVmappleDevice; 14],
    pub(crate) device_count: u32,
    pub(crate) counter: u64,
    pub(crate) gic_state: u32,
    pub(crate) uart_last_byte: u8,
    pub(crate) pvpanic_state: u16,
    pub(crate) storage_state: u32,
    pub(crate) display_state: u32,
    pub(crate) reset_generation: u32,
}

impl VfVmappleMachine {
    pub(crate) fn new(cpu_count: u32, ram_bytes: u64, ecid: u64) -> Option<Self> {
        if cpu_count == 0
            || cpu_count > VMAPPLE_MAX_CPUS
            || ram_bytes == 0
            || ram_bytes & 0xfff != 0
        {
            return None;
        }
        let mut machine = Self {
            cpu_count,
            ram_base: VMAPPLE_RAM_BASE,
            ram_bytes,
            ecid,
            devices: [VfVmappleDevice::EMPTY; 14],
            device_count: 0,
            counter: 0,
            gic_state: GIC_ENABLE,
            uart_last_byte: 0,
            pvpanic_state: 0,
            storage_state: BDIF_READY,
            display_state: DISPLAY_READY,
            reset_generation: 0,
        };
        let entries = [
            (
                VfVmappleDeviceKind::Firmware,
                VMAPPLE_FIRMWARE_BASE,
                VMAPPLE_FIRMWARE_BYTES,
            ),
            (
                VfVmappleDeviceKind::Config,
                VMAPPLE_CONFIG_BASE,
                VMAPPLE_CONFIG_BYTES,
            ),
            (
                VfVmappleDeviceKind::Gic,
                VMAPPLE_GIC_BASE,
                VMAPPLE_GIC_BYTES,
            ),
            (
                VfVmappleDeviceKind::Uart,
                VMAPPLE_UART_BASE,
                VMAPPLE_UART_BYTES,
            ),
            (
                VfVmappleDeviceKind::Rtc,
                VMAPPLE_RTC_BASE,
                VMAPPLE_RTC_BYTES,
            ),
            (
                VfVmappleDeviceKind::Gpio,
                VMAPPLE_GPIO_BASE,
                VMAPPLE_GPIO_BYTES,
            ),
            (
                VfVmappleDeviceKind::Pvpanic,
                VMAPPLE_PVPANIC_BASE,
                VMAPPLE_PVPANIC_BYTES,
            ),
            (
                VfVmappleDeviceKind::Storage,
                VMAPPLE_BDIF_BASE,
                VMAPPLE_BDIF_BYTES,
            ),
            (
                VfVmappleDeviceKind::Display,
                VMAPPLE_DISPLAY_BASE,
                VMAPPLE_DISPLAY_BYTES,
            ),
            (
                VfVmappleDeviceKind::DisplayControl,
                VMAPPLE_DISPLAY_CONTROL_BASE,
                VMAPPLE_DISPLAY_CONTROL_BYTES,
            ),
            // These windows are present in the QEMU VMApple address map.  No
            // register or DMA success is invented here: reads are zero and
            // writes are rejected until a target-matched contract exists.
            (
                VfVmappleDeviceKind::Aes,
                VMAPPLE_AES_BASE,
                VMAPPLE_AES_BYTES,
            ),
            (
                VfVmappleDeviceKind::AesControl,
                VMAPPLE_AES_CONTROL_BASE,
                VMAPPLE_AES_CONTROL_BYTES,
            ),
            (
                VfVmappleDeviceKind::PcieEcam,
                VMAPPLE_PCIE_ECAM_BASE,
                VMAPPLE_PCIE_ECAM_BYTES,
            ),
            (
                VfVmappleDeviceKind::PcieMmio,
                VMAPPLE_PCIE_MMIO_BASE,
                VMAPPLE_PCIE_MMIO_BYTES,
            ),
        ];
        for (kind, base, bytes) in entries {
            machine.devices[machine.device_count as usize] = VfVmappleDevice { kind, base, bytes };
            machine.device_count += 1;
        }
        machine.reset();
        Some(machine)
    }

    pub(crate) fn reset(&mut self) {
        self.counter = 0;
        self.gic_state = GIC_ENABLE;
        self.uart_last_byte = 0;
        self.pvpanic_state = 0;
        self.storage_state = BDIF_READY;
        self.display_state = DISPLAY_READY;
        self.reset_generation = self.reset_generation.saturating_add(1);
    }

    fn device(&self, address: u64, width: u64) -> Option<(VfVmappleDeviceKind, u64)> {
        self.devices[..self.device_count as usize]
            .iter()
            .find(|device| device.contains(address, width))
            .map(|device| (device.kind, address - device.base))
    }

    pub(crate) fn read(&mut self, address: u64, width: u32) -> Option<u64> {
        let bytes = u64::from(width);
        if !matches!(width, 1 | 2 | 4 | 8) || address & (bytes - 1) != 0 {
            return None;
        }
        let (kind, offset) = self.device(address, bytes)?;
        let value = match kind {
            VfVmappleDeviceKind::Firmware => 0,
            VfVmappleDeviceKind::Config => match offset {
                0x000 => u64::from(VMAPPLE_CONFIG_VERSION),
                0x004 => u64::from(self.cpu_count),
                0x018 => self.ecid,
                0x020 => self.ram_bytes,
                0x100 => 0,
                0x3c0 => 0x3130_3030_3030_4d56, // "VM0001" in the fixed-width field
                _ => 0,
            },
            VfVmappleDeviceKind::Gic => match offset {
                0x000 => u64::from(self.gic_state),
                0x004 => u64::from(self.gic_state & GIC_PENDING),
                _ => 0,
            },
            VfVmappleDeviceKind::Uart => match offset {
                0x000 => u64::from(self.uart_last_byte),
                0x018 => u64::from(UART_FR_TXFE | UART_FR_RXFE),
                _ => 0,
            },
            VfVmappleDeviceKind::Rtc => {
                self.counter = self.counter.wrapping_add(1);
                match offset {
                    0x000 => 24_000_000,
                    0x008 => self.counter,
                    _ => 0,
                }
            }
            VfVmappleDeviceKind::Gpio => 0,
            VfVmappleDeviceKind::Pvpanic => u64::from(self.pvpanic_state),
            VfVmappleDeviceKind::Storage => u64::from(self.storage_state),
            VfVmappleDeviceKind::Display | VfVmappleDeviceKind::DisplayControl => {
                u64::from(self.display_state)
            }
            VfVmappleDeviceKind::Aes
            | VfVmappleDeviceKind::AesControl
            | VfVmappleDeviceKind::PcieEcam
            | VfVmappleDeviceKind::PcieMmio => 0,
        };
        Some(value & width_mask(width))
    }

    pub(crate) fn write(&mut self, address: u64, width: u32, value: u64) -> bool {
        let bytes = u64::from(width);
        if !matches!(width, 1 | 2 | 4 | 8) || address & (bytes - 1) != 0 {
            return false;
        }
        let Some((kind, offset)) = self.device(address, bytes) else {
            return false;
        };
        match kind {
            VfVmappleDeviceKind::Firmware
            | VfVmappleDeviceKind::Config
            | VfVmappleDeviceKind::Gpio
            | VfVmappleDeviceKind::Aes
            | VfVmappleDeviceKind::AesControl
            | VfVmappleDeviceKind::PcieEcam
            | VfVmappleDeviceKind::PcieMmio => false,
            VfVmappleDeviceKind::Gic => match offset {
                0x000 => {
                    self.gic_state = (value as u32) & (GIC_ENABLE | GIC_PENDING);
                    true
                }
                0x004 => {
                    self.gic_state &= !(value as u32 & GIC_PENDING);
                    true
                }
                _ => false,
            },
            VfVmappleDeviceKind::Uart => {
                if offset == 0 && width == 1 {
                    self.uart_last_byte = value as u8;
                    true
                } else {
                    false
                }
            }
            VfVmappleDeviceKind::Rtc => false,
            VfVmappleDeviceKind::Pvpanic => {
                if offset == 0 && width <= 2 {
                    self.pvpanic_state = value as u16;
                    true
                } else {
                    false
                }
            }
            VfVmappleDeviceKind::Storage => {
                if offset == 0x408 && width == 8 {
                    self.storage_state = BDIF_READY;
                    true
                } else {
                    false
                }
            }
            VfVmappleDeviceKind::Display | VfVmappleDeviceKind::DisplayControl => {
                if offset == 0 && width == 4 {
                    self.display_state = (value as u32) & DISPLAY_READY;
                    true
                } else {
                    false
                }
            }
        }
    }

    pub(crate) fn valid(&self) -> bool {
        self.cpu_count != 0
            && self.cpu_count <= VMAPPLE_MAX_CPUS
            && self.ram_base == VMAPPLE_RAM_BASE
            && self.ram_bytes != 0
            && self.device_count == self.devices.len() as u32
            && self.reset_generation != 0
    }
}

fn width_mask(width: u32) -> u64 {
    match width {
        1 => 0xff,
        2 => 0xffff,
        4 => 0xffff_ffff,
        8 => u64::MAX,
        _ => 0,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn graph_has_fixed_guest_visible_devices_and_reset() {
        let mut machine = VfVmappleMachine::new(2, 0x4000_0000, 0x1234).unwrap();
        assert!(machine.valid());
        assert_eq!(machine.read(VMAPPLE_CONFIG_BASE, 4), Some(2));
        assert_eq!(machine.read(VMAPPLE_CONFIG_BASE + 0x018, 8), Some(0x1234));
        assert_eq!(
            machine.read(VMAPPLE_UART_BASE + 0x018, 4),
            Some(u64::from(UART_FR_TXFE | UART_FR_RXFE))
        );
        assert!(machine.write(VMAPPLE_UART_BASE, 1, b'V' as u64));
        assert_eq!(machine.uart_last_byte, b'V');
        assert!(machine.write(VMAPPLE_PVPANIC_BASE, 2, 1));
        assert_eq!(machine.pvpanic_state, 1);
        assert_eq!(machine.read(VMAPPLE_AES_BASE, 4), Some(0));
        assert_eq!(machine.read(VMAPPLE_PCIE_ECAM_BASE, 4), Some(0));
        assert!(!machine.write(VMAPPLE_AES_BASE, 4, 1));
        assert!(!machine.write(VMAPPLE_PCIE_MMIO_BASE, 4, 1));
        let generation = machine.reset_generation;
        machine.reset();
        assert!(machine.reset_generation > generation);
        assert_eq!(machine.pvpanic_state, 0);
        assert_eq!(machine.storage_state, BDIF_READY);
    }

    #[test]
    fn invalid_width_alignment_and_unknown_registers_fail_closed() {
        let mut machine = VfVmappleMachine::new(1, 0x4000_0000, 0).unwrap();
        assert_eq!(machine.read(VMAPPLE_UART_BASE + 1, 4), None);
        assert_eq!(machine.read(VMAPPLE_UART_BASE, 16), None);
        assert!(!machine.write(VMAPPLE_CONFIG_BASE, 4, 1));
        assert!(!machine.write(VMAPPLE_UART_BASE + 4, 4, 1));
        assert!(!machine.write(VMAPPLE_FIRMWARE_BASE, 4, 1));
        assert_eq!(
            machine.read(VMAPPLE_PCIE_MMIO_BASE + VMAPPLE_PCIE_MMIO_BYTES, 4),
            None
        );
        assert_eq!(machine.read(0xdead_0000, 4), None);
    }
}
