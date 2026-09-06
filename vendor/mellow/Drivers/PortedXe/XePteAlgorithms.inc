// SPDX-License-Identifier: MIT
/*
 * Copyright © 2021 Intel Corporation
 * Selected upstream functions; see provenance.json and LICENSE.MIT.
 * Compatibility definitions are in XePageTable.cpp; bodies below are verbatim.
 */

/* Source xe_ggtt.c:146; function body preserved verbatim. */
static u64 xelp_ggtt_pte_flags(struct xe_bo *bo, u16 pat_index)
{
	u64 pte = XE_PAGE_PRESENT;

	if (xe_bo_is_vram(bo) || xe_bo_is_stolen_devmem(bo))
		pte |= XE_GGTT_PTE_DM;

	return pte;
}

/* Source xe_ggtt.c:156; function body preserved verbatim. */
static u64 xelpg_ggtt_pte_flags(struct xe_bo *bo, u16 pat_index)
{
	struct xe_device *xe = xe_bo_device(bo);
	u64 pte;

	pte = xelp_ggtt_pte_flags(bo, pat_index);

	xe_assert(xe, pat_index <= 3);

	if (pat_index & BIT(0))
		pte |= XELPG_GGTT_PTE_PAT0;

	if (pat_index & BIT(1))
		pte |= XELPG_GGTT_PTE_PAT1;

	return pte;
}

/* Source xe_vm.c:1375; function body preserved verbatim. */
static u64 pde_encode_pat_index(u16 pat_index)
{
	u64 pte = 0;

	if (pat_index & BIT(0))
		pte |= XE_PPGTT_PTE_PAT0;

	if (pat_index & BIT(1))
		pte |= XE_PPGTT_PTE_PAT1;

	return pte;
}

/* Source xe_vm.c:1388; function body preserved verbatim. */
static u64 pte_encode_pat_index(u16 pat_index, u32 pt_level)
{
	u64 pte = 0;

	if (pat_index & BIT(0))
		pte |= XE_PPGTT_PTE_PAT0;

	if (pat_index & BIT(1))
		pte |= XE_PPGTT_PTE_PAT1;

	if (pat_index & BIT(2)) {
		if (pt_level)
			pte |= XE_PPGTT_PDE_PDPE_PAT2;
		else
			pte |= XE_PPGTT_PTE_PAT2;
	}

	if (pat_index & BIT(3))
		pte |= XELPG_PPGTT_PTE_PAT3;

	if (pat_index & (BIT(4)))
		pte |= XE2_PPGTT_PTE_PAT4;

	return pte;
}

/* Source xe_vm.c:1414; function body preserved verbatim. */
static u64 pte_encode_ps(u32 pt_level)
{
	XE_WARN_ON(pt_level > MAX_HUGEPTE_LEVEL);

	if (pt_level == 1)
		return XE_PDE_PS_2M;
	else if (pt_level == 2)
		return XE_PDPE_PS_1G;

	return 0;
}

/* Source xe_vm.c:1505; function body preserved verbatim. */
static u64 xelp_pte_encode_addr(struct xe_device *xe, u64 addr,
				u16 pat_index,
				u32 pt_level, bool devmem, u64 flags)
{
	u64 pte;

	/* Avoid passing random bits directly as flags */
	xe_assert(xe, !(flags & ~XE_PTE_PS64));

	pte = addr;
	pte |= XE_PAGE_PRESENT | XE_PAGE_RW;
	pte |= pte_encode_pat_index(pat_index, pt_level);
	pte |= pte_encode_ps(pt_level);

	if (devmem)
		pte |= XE_PPGTT_PTE_DM;

	pte |= flags;

	return pte;
}
