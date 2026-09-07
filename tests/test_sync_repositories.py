import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Tools"))
import importlib.util
spec = importlib.util.spec_from_file_location("sync_mod", str(Path(__file__).resolve().parents[1] / "Tools" / "sync_github_repositories.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SyncContract(unittest.TestCase):
    def test_legacy_prefix_exact(self):
        self.assertTrue(mod.legacy_tag_is_removable("26x86-VenFire-GoldenGate-v0.1.0"))
        self.assertFalse(mod.legacy_tag_is_removable("26x86-VenFire-v0.1.0"))
        self.assertFalse(mod.legacy_tag_is_removable("26x86-VenFire-GoldenGate-v".lower()))
    def test_plan_lists_both_modules(self):
        plans = [{"directory": "/tmp/a/VenFire", "metadata": {"name": "VenFire", "initial_tag": "t1"}},
                 {"directory": "/tmp/a/VenFire-QEMU", "metadata": {"name": "VenFire-QEMU", "initial_tag": "t2"}}]
        actions = mod.plan_actions(plans)
        self.assertTrue(any("26x86/VenFire-QEMU" in a for a in actions))
        self.assertTrue(any("GoldenGate" in a for a in actions))
    def test_owner_is_organization(self):
        self.assertEqual(mod.OWNER, "26x86")
        self.assertEqual(mod.CORE_REPOSITORY, "26x86")

if __name__ == "__main__":
    unittest.main()
