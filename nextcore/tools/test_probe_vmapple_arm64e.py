"""Evidence rejection tests for the real VMApple architectural CPU probe."""
import unittest

from probe_vmapple_arm64e import evaluate, registers


class CpuEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.before = "X00=0000000000000000 X20=0000000000000000\n"
        self.values = {
            0: 0x64E, 4: 0x100164, 10: 0x1357, 11: 0x2468,
            12: 0x1357, 13: 0x2468, 19: 0, 20: 0x7F, 21: 4,
            22: 0x10, 23: 0x100000, 24: 24_000_000, 25: 100,
            26: 200, 27: 0, 28: 0xFA00000000100164,
        }

    def snapshot(self):
        return " ".join(f"X{number:02}={value:016x}" for number, value in self.values.items()) + "\n"

    def test_complete_observations(self):
        self.assertTrue(evaluate(self.before, self.snapshot(), 0)["passed"])

    def test_bitmap_without_register_observations_rejected(self):
        for number in (4, 10, 11, 12, 13, 21, 22, 23, 24, 25, 26, 27, 28):
            with self.subTest(register=number):
                saved = self.values.pop(number)
                self.assertFalse(evaluate(self.before, self.snapshot(), 0)["passed"])
                self.values[number] = saved

    def test_cpu_contract_mismatches_rejected(self):
        for number, value in ((21, 8), (22, 0), (23, 0), (24, 1), (26, 100),
                              (12, 9), (13, 9), (27, 1), (28, self.values[4])):
            with self.subTest(register=number):
                saved = self.values[number]
                self.values[number] = value
                self.assertFalse(evaluate(self.before, self.snapshot(), 0)["passed"])
                self.values[number] = saved

    def test_old_result_and_nonzero_exit_rejected(self):
        self.assertFalse(evaluate(self.snapshot(), self.snapshot(), 0)["passed"])
        self.assertFalse(evaluate(self.before, self.snapshot(), -15)["passed"])

    def test_incomplete_guest_rejected(self):
        for number, value in ((0, 0xBAD), (19, 7), (20, 0x3F), (20, 0xFF)):
            with self.subTest(register=number):
                saved = self.values[number]
                self.values[number] = value
                self.assertFalse(evaluate(self.before, self.snapshot(), 0)["passed"])
                self.values[number] = saved

    def test_register_width_and_duplicate_rejected(self):
        self.assertEqual(registers("X0=64e X20=7f\n"), {0: 0x64E, 20: 0x7F})
        self.assertEqual(registers("X0=1000000000000064e\n"), {})
        with self.assertRaises(ValueError):
            registers("X00=1 X0=2\n")


if __name__ == "__main__":
    unittest.main()
