use crate::error::HalError;

#[derive(Debug, Clone)]
pub struct AcpiPatchDef {
    pub offset: usize,
    pub length: usize,
    pub data: Vec<u8>,
}

pub struct AcpiTranslator;

impl AcpiTranslator {
    pub fn new() -> Self {
        Self
    }

    pub fn patch_dsdt(real_dsdt: &[u8], patches: &[AcpiPatchDef]) -> Result<Vec<u8>, HalError> {
        let mut result = real_dsdt.to_vec();

        for patch in patches {
            let end = patch.offset + patch.length;
            if end > result.len() {
                return Err(HalError::PatchOutOfBounds {
                    offset: patch.offset,
                    length: patch.length,
                    dsdt_len: real_dsdt.len(),
                });
            }
            if patch.data.len() != patch.length {
                return Err(HalError::PatchLengthMismatch {
                    expected: patch.length,
                    actual: patch.data.len(),
                });
            }
            result[patch.offset..end].copy_from_slice(&patch.data);
        }

        log::info!(
            "DSDT patched: {} patches applied to {} bytes",
            patches.len(),
            real_dsdt.len()
        );
        Ok(result)
    }

    pub fn apply_patches(data: &[u8], patches: &[AcpiPatchDef]) -> Result<Vec<u8>, HalError> {
        Self::patch_dsdt(data, patches)
    }
}

impl Default for AcpiTranslator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_patch_dsdt() {
        let dsdt = vec![0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
        let patches = vec![AcpiPatchDef {
            offset: 2,
            length: 2,
            data: vec![0xAA, 0xBB],
        }];
        let result = AcpiTranslator::patch_dsdt(&dsdt, &patches).unwrap();
        assert_eq!(result, vec![0, 1, 0xAA, 0xBB, 4, 5, 6, 7, 8, 9]);
    }
}
