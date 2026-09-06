"""Opt-in Mellow data-volume driver payload; not a GPU acceleration verdict."""
from ..base import BaseHardware, HardwareVariant
from x86.mellow.integration import selected_payload


class Mellow(BaseHardware):
    def name(self):
        return f"{self.hardware_variant()}: Mellow"

    def hardware_variant(self):
        return HardwareVariant.MISCELLANEOUS

    def present(self):
        return selected_payload(self._constants) is not None

    def native_os(self):
        return False

    def requires_kernel_debug_kit(self):
        # Preserve the actual payload's OSBundleRequired=Safe Boot. It cannot
        # be relabelled Auxiliary merely to avoid the primary collection.
        return True

    def requires_primary_kernel_cache(self):
        return True

    def patches(self):
        payload = selected_payload(self._constants)
        if payload is None:
            return {}
        if self._xnu_major != 25:
            raise ValueError("Bundled Mellow diagnostic driver requires Darwin 25")
        return payload.patches()
