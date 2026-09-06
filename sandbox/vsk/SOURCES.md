# VSK implementation sources

Policy, message layout, budgets and layer boundaries come from the user-adopted
VF-SPEC-001 v0.1, not from measurements of completed hardware support.

- Intel SDM, edition 092 listed on 2026-09-06:
  https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html
  VMX allowed-control bit interpretation, ISA and XSTATE definitions. Policy
  helpers consuming captured values are not live MSR probes or VMX enablement.
- ACPICA's Intel-maintained `actbl1.h`, DMAR structure definitions:
  https://github.com/acpica/acpica/blob/master/source/include/actbl1.h
  Used to verify DMAR/DRHD/RMRR/device-scope binary offsets; no source copied.
  The parser intentionally rejects unimplemented structures/extensions.
- Intel VT-d architecture specification, section 8.5 (ATSR scope restrictions):
  https://cdrdv2-public.intel.com/774206/vt-directed-io-spec%20.pdf
  ATSR device scopes identify PCI sub-hierarchies; endpoint/IOAPIC/HPET scopes
  are rejected in ATSR even though those types occur in other DMAR structures.
- UEFI specification, memory descriptors and Boot Services lifetime:
  https://uefi.org/specs/UEFI/2.11/
  A copied memory map and structurally valid handoff do not establish ownership
  unless the caller obtained buffers through the trusted loader allocator.

These references establish hardware facts, not VSK implementation completion.
First-party code uses the repository license; third-party code or firmware
imports require their own provenance and retained license terms.
