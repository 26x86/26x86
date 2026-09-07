use goblin::mach::Mach;

use crate::error::{CoreError, Result};

#[derive(Debug, Clone)]
pub struct MachOHeader {
    pub magic: u32,
    pub filetype: u32,
    pub cpu_type: u32,
    pub cpu_subtype: u32,
    pub ncmds: usize,
    pub sizeofcmds: u32,
    pub entry_offset: u64,
    pub segments: Vec<MachOSegment>,
}

#[derive(Debug, Clone)]
pub struct MachOSegment {
    pub name: String,
    pub vmaddr: u64,
    pub vmsize: u64,
    pub fileoff: u64,
    pub filesize: u64,
}

pub struct MachOLoader;

impl MachOLoader {
    pub fn parse_header(data: &[u8]) -> Result<MachOHeader> {
        let mach = Mach::parse(data)
            .map_err(|e| CoreError::MachO(format!("goblin parse failed: {e}")))?;

        match mach {
            Mach::Binary(macho) => {
                let header = &macho.header;
                let mut segments = Vec::new();

                for seg in &macho.segments {
                    let name = std::str::from_utf8(&seg.segname[..])
                        .unwrap_or("")
                        .trim_end_matches('\0')
                        .to_string();
                    segments.push(MachOSegment {
                        name,
                        vmaddr: seg.vmaddr,
                        vmsize: seg.vmsize,
                        fileoff: seg.fileoff,
                        filesize: seg.filesize,
                    });
                }

                let entry_offset = find_entry_offset(data)?;

                Ok(MachOHeader {
                    magic: header.magic,
                    filetype: header.filetype,
                    cpu_type: header.cputype,
                    cpu_subtype: header.cpusubtype,
                    ncmds: header.ncmds,
                    sizeofcmds: header.sizeofcmds,
                    entry_offset,
                    segments,
                })
            }
            Mach::Fat(_) => Err(CoreError::MachO(
                "fat binaries not supported, extract first".into(),
            )),
        }
    }
}

pub fn calculate_entry_address(header: &MachOHeader) -> Result<u64> {
    let base = header
        .segments
        .iter()
        .map(|s| s.vmaddr)
        .min()
        .unwrap_or(0);
    Ok(base.wrapping_add(header.entry_offset))
}

fn find_entry_offset(data: &[u8]) -> Result<u64> {
    let mach =
        Mach::parse(data).map_err(|e| CoreError::MachO(format!("goblin parse failed: {e}")))?;

    if let Mach::Binary(macho) = mach {
        for cmd in &macho.load_commands {
            if let goblin::mach::load_command::CommandVariant::Main(main_cmd) = cmd.command {
                return Ok(main_cmd.entryoff);
            }
        }
    }

    Ok(0)
}
