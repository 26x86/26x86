"""Offline proofs for original-preserving VMApple personalization helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile


class VMapplePersonalizationTests(unittest.TestCase):
    def test_img4_wrap_preserves_original_im4p_bytes(self) -> None:
        from x86.vmapple_personalization import _der, wrap_firmware

        payload = _der(0x30, _der(0x16, b"IM4P") + _der(0x16, b"ibss") + b"ORIGINAL")
        ticket = _der(0x30, _der(0x16, b"IM4M") + b"TICKET")
        wrapped = wrap_firmware(payload, ticket, "iBSS")
        self.assertIn(payload, wrapped)
        self.assertIn(ticket, wrapped)

    def test_img4_wrap_rejects_wrong_component_tag(self) -> None:
        from x86.vmapple_personalization import _der, wrap_firmware

        payload = _der(0x30, _der(0x16, b"IM4P") + _der(0x16, b"ibec") + b"ORIGINAL")
        ticket = _der(0x30, _der(0x16, b"IM4M") + b"TICKET")
        with self.assertRaises(ValueError):
            wrap_firmware(payload, ticket, "iBSS")

    def test_live_mode_requires_explicit_original_inputs(self) -> None:
        from x86.vmapple import VMappleConfig

        class FakeExecutable:
            is_wsl = False

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("firmware", "aux", "root"):
                (root / name).write_bytes(b"x" * 512)
            config = VMappleConfig(
                target_major=27, qemu="qemu", firmware=str(root / "firmware"), ibss="",
                aux=str(root / "aux"), root=str(root / "root"), research_only=True,
                live_personalize=True,
            )
            with patch("x86.vmapple._resolve_executable", return_value=FakeExecutable()):
                with self.assertRaisesRegex(ValueError, "BuildManifest"):
                    config.validate()

    def test_non_developer_personalization_is_rejected_before_socket_access(self) -> None:
        from x86.vmapple_personalization import _authorization

        with self.assertRaisesRegex(RuntimeError, "research-only"):
            _authorization(False)


if __name__ == "__main__":
    unittest.main()
