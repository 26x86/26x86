/* SPDX-License-Identifier: BSD-4-Clause. Own-code loader fixture, not a kernel. */
volatile unsigned vf_fixture_bss[16];
volatile unsigned vf_fixture_data=7;
unsigned vf_fixture_entry(void) { return vf_fixture_bss[0]+vf_fixture_data+35; }
