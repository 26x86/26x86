use bitflags::bitflags;

bitflags! {
    #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
    pub struct CpuFeatureSet: u64 {
        const SSE        = 1 << 0;
        const SSE2       = 1 << 1;
        const SSE3       = 1 << 2;
        const SSSE3      = 1 << 3;
        const SSE4_1     = 1 << 4;
        const SSE4_2     = 1 << 5;
        const AVX        = 1 << 6;
        const AVX2       = 1 << 7;
        const FMA        = 1 << 8;
        const POPCNT     = 1 << 9;
        const BMI1       = 1 << 10;
        const BMI2       = 1 << 11;
        const AES_NI     = 1 << 12;
        const PCLMULQDQ  = 1 << 13;
        const OSXSAVE    = 1 << 14;
    }
}

#[derive(Debug, Clone)]
pub struct CpuFeatures {
    pub features: CpuFeatureSet,
    pub max_cpuid_leaf: u32,
    pub max_ext_cpuid_leaf: u32,
    pub brand_string: [u32; 16],
}

impl CpuFeatures {
    #[allow(unused_assignments)]
    pub fn detect() -> Self {
        let mut features = CpuFeatureSet::empty();
        let mut max_cpuid_leaf: u32 = 0;
        let mut max_ext_cpuid_leaf: u32 = 0;
        let mut brand_string = [0u32; 16];

        #[cfg(target_arch = "x86_64")]
        {
            let result = core::arch::x86_64::__cpuid_count(0, 0);
            max_cpuid_leaf = result.eax;

            if max_cpuid_leaf >= 1 {
                let result = core::arch::x86_64::__cpuid_count(1, 0);
                if result.edx & (1 << 25) != 0 { features |= CpuFeatureSet::SSE; }
                if result.edx & (1 << 26) != 0 { features |= CpuFeatureSet::SSE2; }
                if result.ecx & (1 << 0) != 0 { features |= CpuFeatureSet::SSE3; }
                if result.ecx & (1 << 9) != 0 { features |= CpuFeatureSet::SSSE3; }
                if result.ecx & (1 << 19) != 0 { features |= CpuFeatureSet::SSE4_1; }
                if result.ecx & (1 << 20) != 0 { features |= CpuFeatureSet::SSE4_2; }
                if result.ecx & (1 << 28) != 0 { features |= CpuFeatureSet::AVX; }
                if result.ecx & (1 << 12) != 0 { features |= CpuFeatureSet::POPCNT; }
                if result.ecx & (1 << 25) != 0 { features |= CpuFeatureSet::AES_NI; }
                if result.ecx & (1 << 1) != 0 { features |= CpuFeatureSet::PCLMULQDQ; }
                if result.ecx & (1 << 27) != 0 { features |= CpuFeatureSet::OSXSAVE; }
            }

            if max_cpuid_leaf >= 7 {
                let result = core::arch::x86_64::__cpuid_count(7, 0);
                if result.ebx & (1 << 5) != 0 { features |= CpuFeatureSet::AVX2; }
                if result.ebx & (1 << 3) != 0 { features |= CpuFeatureSet::BMI1; }
                if result.ebx & (1 << 8) != 0 { features |= CpuFeatureSet::BMI2; }
            }

            let ext_result = core::arch::x86_64::__cpuid_count(0x80000000, 0);
            max_ext_cpuid_leaf = ext_result.eax;

            if max_ext_cpuid_leaf >= 7 {
                let result = core::arch::x86_64::__cpuid_count(0x80000001, 0);
                if result.ecx & (1 << 12) != 0 { features |= CpuFeatureSet::FMA; }
            }

            if max_ext_cpuid_leaf >= 4 {
                for i in 0..4u32 {
                    let result = core::arch::x86_64::__cpuid_count(0x80000002 + i, 0);
                    brand_string[(i * 4 + 0) as usize] = result.eax;
                    brand_string[(i * 4 + 1) as usize] = result.ebx;
                    brand_string[(i * 4 + 2) as usize] = result.ecx;
                    brand_string[(i * 4 + 3) as usize] = result.edx;
                }
            }
        }

        #[cfg(not(target_arch = "x86_64"))]
        {
            log::warn!("CPUID not available on non-x86_64, returning empty features");
        }

        Self {
            features,
            max_cpuid_leaf,
            max_ext_cpuid_leaf,
            brand_string,
        }
    }

    pub fn has_avx(&self) -> bool {
        self.features.contains(CpuFeatureSet::AVX)
    }

    pub fn has_sse4_1(&self) -> bool {
        self.features.contains(CpuFeatureSet::SSE4_1)
    }

    pub fn has_sse4_2(&self) -> bool {
        self.features.contains(CpuFeatureSet::SSE4_2)
    }

    pub fn has_fma(&self) -> bool {
        self.features.contains(CpuFeatureSet::FMA)
    }

    pub fn missing_features(&self, target: &CpuFeatureSet) -> CpuFeatureSet {
        *target & !self.features
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_runs() {
        let features = CpuFeatures::detect();
        log::info!("Detected features: {:?}", features.features);
    }

    #[test]
    fn test_missing_features() {
        let mut features = CpuFeatures::detect();
        let required = CpuFeatureSet::AVX | CpuFeatureSet::SSE4_2;
        let missing = features.missing_features(&required);

        if features.has_avx() && features.has_sse4_2() {
            assert_eq!(missing, CpuFeatureSet::empty());
        }

        features.features = CpuFeatureSet::empty();
        let missing = features.missing_features(&required);
        assert!(missing.contains(CpuFeatureSet::AVX));
        assert!(missing.contains(CpuFeatureSet::SSE4_2));
    }
}
