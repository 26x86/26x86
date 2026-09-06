/* SPDX-License-Identifier: BSD-4-Clause.
 * Additional CPU edges not duplicated by test_policy's per-bit VMX truth table.
 * All snapshots are synthetic UNIT fixtures, not real CPUID/MSR observations.
 */
#include "vf_policy.h"
#include <stdio.h>
#include <stdlib.h>
static unsigned checks;
#define CHECK(x) do {++checks;if(!(x)){fprintf(stderr,"test_cpu:%d: %s\n",__LINE__,#x);exit(1);}}while(0)
static struct vf_cpu_capability full(uint32_t id) {
    struct vf_cpu_capability c={0};c.logical_id=id;c.max_basic_leaf=13;
    c.leaf1_ecx=(1u<<20)|(1u<<26)|(1u<<27)|(1u<<28);
    c.leaf1_edx=(1u<<24)|(1u<<25)|(1u<<26);c.leaf7_ebx=1u<<5;
    c.ext_80000001_edx=(1u<<20)|(1u<<29);
    c.intel_vendor=c.sse_state_managed=c.xstate_managed=1;
    c.xcr0=c.xstate_save_mask=7;return c;
}
static void baseline_errors(void) {
    struct vf_cpu_capability c=full(0);
    struct vf_codegen_choice result;
    /* Every required legacy save-state/NX/long-mode bit is independently vital. */
    for(unsigned bit=24;bit<=26;bit++) {
        c=full(0);c.leaf1_edx&=~(1u<<bit);result=(struct vf_codegen_choice){99,UINT64_MAX};
        CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
        CHECK(result.tier==0&&result.common_xstate==0);
    }
    const unsigned ext_bits[]={20,29};
    for(unsigned i=0;i<2;i++) {
        c=full(0);c.ext_80000001_edx&=~(1u<<ext_bits[i]);
        CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
    }
    c=full(0);c.max_basic_leaf=0;CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
    c=full(0);c.intel_vendor=2;CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
    c=full(0);c.sse_state_managed=2;CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
    c=full(0);c.xstate_managed=2;CHECK(vf_select_common_codegen(&c,1,&result)==VF_ECPU);
    c=full(0);CHECK(vf_select_common_codegen(&c,VF_POLICY_TABLE_MAX+1,&result)==VF_EINVAL);
    CHECK(vf_select_common_codegen(NULL,1,&result)==VF_EINVAL);
    CHECK(vf_select_common_codegen(&c,1,NULL)==VF_EINVAL);
}
static void domain_edges(void) {
    struct vf_cpu_capability c[3]={full(9),full(42),full(100)}, permutation[3];
    struct vf_codegen_choice result;
    /* Saving x87/SSE/YMM alone is insufficient if root enabled another state. */
    c[0].xcr0|=UINT64_C(1)<<9;
    CHECK(vf_select_common_codegen(c,3,&result)==VF_OK);
    CHECK(result.tier==VF_CODEGEN_SSE42&&result.common_xstate==3);
    c[0].xstate_save_mask=c[0].xcr0;
    CHECK(vf_select_common_codegen(c,3,&result)==VF_OK);
    CHECK(result.tier==VF_CODEGEN_AVX2&&result.common_xstate==7);
    /* Extra saved-but-not-enabled state does not enlarge advertised ISA. */
    c[1].xstate_save_mask=UINT64_MAX;
    CHECK(vf_select_common_codegen(c,3,&result)==VF_OK&&result.common_xstate==7);
    c[1].leaf7_ebx=0;c[2].xstate_managed=0;
    for(unsigned first=0;first<3;first++) for(unsigned second=0;second<3;second++) if(first!=second) {
        permutation[0]=c[first];permutation[1]=c[second];permutation[2]=c[3-first-second];
        CHECK(vf_select_common_codegen(permutation,3,&result)==VF_OK);
        CHECK(result.tier==VF_CODEGEN_SSE42&&result.common_xstate==3);
    }
    /* Missing baseline on a later CPU cannot be hidden by an earlier slow tier. */
    c[0].xstate_managed=0;c[2].ext_80000001_edx=0;
    CHECK(vf_select_common_codegen(c,3,&result)==VF_ECPU&&result.tier==0&&result.common_xstate==0);
}
static void multi_bit_vmx(void) {
    uint64_t msrs[3]={UINT64_C(0xffffffff00000001),UINT64_C(0xffffffff80000000),UINT64_C(0xfffffffd00000000)};
    uint32_t result=0;
    /* CPU0 requires bit0, CPU1 bit31; CPU2 rejects optional bit1 but allows bit2. */
    CHECK(vf_vmx_combine_controls(msrs,3,1,6,0,&result)==VF_OK);
    CHECK(result==UINT32_C(0x80000005));
    CHECK(vf_vmx_combine_controls(msrs,3,1,6,2,&result)==VF_EINVAL&&result==0);
    CHECK(vf_vmx_combine_controls(msrs,3,2,4,0,&result)==VF_EVMX&&result==0);
    CHECK(vf_vmx_combine_controls(msrs,3,0,4,UINT32_C(0x80000000),&result)==VF_EVMX&&result==0);
    msrs[2]=UINT64_C(0x7fffffff00000000);
    CHECK(vf_vmx_combine_controls(msrs,3,0,0,0,&result)==VF_EVMX&&result==0);
    CHECK(vf_vmx_combine_controls(msrs,VF_POLICY_TABLE_MAX+1,0,0,0,&result)==VF_EINVAL);
    CHECK(vf_vmx_combine_controls(NULL,1,0,0,0,&result)==VF_EINVAL);
    CHECK(vf_vmx_combine_controls(msrs,1,0,0,0,NULL)==VF_EINVAL);
    const uint64_t high=UINT64_C(1)<<63;
    CHECK(vf_vmx_validate_fixed_bits(high|1,high,high|3)==VF_OK);
    CHECK(vf_vmx_validate_fixed_bits(1,high,high|3)==VF_EVMX);
    CHECK(vf_vmx_validate_fixed_bits(high|4,high,high|3)==VF_EVMX);
    CHECK(vf_vmx_validate_fixed_bits(high,high,3)==VF_EVMX);
    CHECK(vf_vmx_validate_fixed_bits(UINT64_MAX,UINT64_MAX,UINT64_MAX)==VF_OK);
}
int main(void) {
    baseline_errors();domain_edges();multi_bit_vmx();
    printf("{\"test\":\"cpu\",\"level\":\"UNIT\",\"passed\":true,\"checks\":%u,\"hardware_verified\":false}\n",checks);
    return 0;
}
