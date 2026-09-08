//! Host-side receipt adapter: inspect exact NXHAL bytes using the public HAL API.
//! Success means byte decoding, not guest device publication or OS acceptance.

use nextcore_hal::{acpi_raw::*, pci_raw::decode_config_space};
use serde_json::{json, Value};
use std::{error::Error, ffi::OsString};

fn inspect(kind: &str, bytes: &[u8]) -> Result<Value, Box<dyn Error>> {
    match kind {
        "RSDP" => {
            let info = parse_rsdp(bytes)?;
            Ok(json!({
                "kind": "RSDP",
                "length": info.length,
                "checksum_ok": info.checksum_ok && info.extended_checksum_ok,
                "summary": {
                    "revision": info.revision,
                    "rsdt_address": info.rsdt_address,
                    "xsdt_address": info.xsdt_address,
                },
            }))
        }
        "SDT" => {
            let header = parse_sdt_header(bytes)?;
            if !header.checksum_ok {
                return Err("SDT checksum nonzero".into());
            }
            let summary = match &header.signature {
                b"XSDT" => {
                    let addresses = parse_xsdt_addresses(bytes)?;
                    json!({"entry_count": addresses.len(), "addresses": addresses})
                }
                b"RSDT" => {
                    let addresses = parse_rsdt_addresses(bytes)?;
                    json!({"entry_count": addresses.len(), "addresses": addresses})
                }
                b"APIC" => {
                    let info = parse_madt_summary(bytes)?;
                    json!({
                        "total_entries": info.total_entries,
                        "lapic": info.lapic,
                        "ioapic": info.ioapic,
                        "interrupt_override": info.interrupt_override,
                        "nmi": info.nmi,
                        "lapic_address_override": info.lapic_address_override,
                        "other": info.other,
                        "local_apic_address": info.local_apic_address,
                        "flags": info.flags,
                    })
                }
                b"MCFG" => {
                    let info = parse_mcfg_summary(bytes)?;
                    json!({"segment_groups": info.segment_groups})
                }
                b"FACP" => {
                    let info = parse_facp_summary(bytes)?;
                    json!({
                        "dsdt": info.dsdt,
                        "x_dsdt": info.x_dsdt,
                        "smi_cmd": info.smi_cmd,
                        "acpi_enable": info.acpi_enable,
                    })
                }
                // E.g. HPET: generic SDT header/length/checksum validation only.
                // Never imply that this adapter decodes the device register ABI.
                _ => Value::Null,
            };
            Ok(json!({
                "kind": "SDT",
                "signature": header.signature_str,
                "length": header.length,
                "revision": header.revision,
                "checksum_ok": true,
                "summary": summary,
            }))
        }
        "PCI" => {
            let device = decode_config_space(bytes)?;
            Ok(json!({
                "kind": "PCI",
                "length": 64,
                "header_type": bytes[0x0e] & 0x7f,
                "multifunction": bytes[0x0e] & 0x80 != 0,
                "vendor_id": device.vendor_id,
                "device_id": device.device_id,
                "revision": device.revision,
                "class_code": device.class_code,
                "subclass": device.subclass,
                "prog_if": device.prog_if,
                "subsystem_vendor_id": device.subsystem_vendor_id,
                "subsystem_device_id": device.subsystem_device_id,
            }))
        }
        _ => Err("kind must be RSDP, SDT, or PCI".into()),
    }
}

fn run(mut args: impl Iterator<Item = OsString>) -> Result<(), Box<dyn Error>> {
    let usage = "usage: inspect_firmware <RSDP|SDT|PCI> <binary-file>";
    let kind = args.next().ok_or(usage)?;
    let path = args.next().ok_or(usage)?;
    if args.next().is_some() {
        return Err(usage.into());
    }
    let kind = kind.to_str().ok_or("kind must be ASCII")?;
    let bytes = std::fs::read(path)?;
    let report = inspect(kind, &bytes)?;
    println!("{}", serde_json::to_string(&report)?);
    Ok(())
}

fn main() {
    if let Err(error) = run(std::env::args_os().skip(1)) {
        eprintln!("inspect_firmware: {error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sdt(signature: &[u8; 4], body: &[u8]) -> Vec<u8> {
        let mut bytes = vec![0; 36];
        bytes.extend_from_slice(body);
        bytes[..4].copy_from_slice(signature);
        let len = bytes.len() as u32;
        bytes[4..8].copy_from_slice(&len.to_le_bytes());
        bytes[9] = 0u8.wrapping_sub(bytes.iter().fold(0u8, |a, b| a.wrapping_add(*b)));
        bytes
    }

    #[test]
    fn reports_root_addresses_as_json_integers() {
        let report = inspect(
            "SDT",
            &sdt(b"XSDT", &0x1234_5678_9abc_def0u64.to_le_bytes()),
        )
        .unwrap();
        assert_eq!(report["summary"]["addresses"][0], 0x1234_5678_9abc_def0u64);
        assert_eq!(report["summary"]["entry_count"], 1);
        assert_eq!(report["checksum_ok"], true);
    }

    #[test]
    fn adapter_rejects_bad_checksum_and_typed_structure() {
        let mut bytes = sdt(b"HPET", &[0; 20]);
        bytes[9] ^= 1;
        assert!(inspect("SDT", &bytes).is_err());
        assert!(inspect("SDT", &sdt(b"APIC", &[0; 9])).is_err());
        assert!(inspect("SDT", &sdt(b"MCFG", &[0; 9])).is_err());
    }

    #[test]
    fn generic_table_reports_no_device_specific_summary() {
        let report = inspect("SDT", &sdt(b"HPET", &[0; 20])).unwrap();
        assert_eq!(report["signature"], "HPET");
        assert!(report["summary"].is_null());
    }

    #[test]
    fn pci_report_preserves_ids_without_translator_policy() {
        let mut bytes = [0u8; 64];
        bytes[..4].copy_from_slice(&[0x34, 0x12, 0x78, 0x56]);
        bytes[0x0e] = 0x80;
        bytes[44..48].copy_from_slice(&[0xbc, 0x9a, 0xf0, 0xde]);
        let report = inspect("PCI", &bytes).unwrap();
        assert_eq!(report["vendor_id"], 0x1234);
        assert_eq!(report["subsystem_vendor_id"], 0x9abc);
        assert_eq!(report["subsystem_device_id"], 0xdef0);
        assert_eq!(report["multifunction"], true);
        bytes[0x0e] = 0x81;
        assert!(inspect("PCI", &bytes).is_err());
    }

    #[test]
    fn invalid_invocation_is_an_error() {
        assert!(run(std::iter::empty()).is_err());
        assert!(inspect("OTHER", &[]).is_err());
    }
}
