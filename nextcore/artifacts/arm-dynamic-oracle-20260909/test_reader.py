#!/usr/bin/env python3
"""Strict-reader regression controls against saved actual authored Arm logs."""
from pathlib import Path
import argparse, unittest
import probe_enable as reader

class StrictReaderTests(unittest.TestCase):
    def load(self,name):
        return (CAPTURE/(name+".log")).read_text()
    def test_normal_six_actual_cases(self):
        cases=reader.parse(self.load("normal"))
        self.assertEqual([c["name"] for c in cases],reader.NAMES)
        self.assertTrue(all(c["passed"] for c in cases))
    def test_duplicate_record_rejected(self):
        text=self.load("normal")
        with self.assertRaisesRegex(ValueError,"duplicate record"):
            reader.parse(text+"\n"+text.splitlines()[0]+"\n")
    def test_missing_case_rejected(self):
        text="\n".join(x for x in self.load("normal").splitlines()
                       if not x.startswith("g16384_data_unmapped "))
        with self.assertRaises(KeyError):reader.parse(text)
    def test_malformed_number_rejected(self):
        text=self.load("normal").replace("HCR 0000000080000000","HCR NaN",1)
        with self.assertRaisesRegex(ValueError,"malformed numeric"):reader.parse(text)
    def test_wrong_fault_level_does_not_pass(self):
        text=self.load("normal").replace("g4096_fetch_unmapped 0000000086000007",
                                        "g4096_fetch_unmapped 0000000086000006",1)
        cases=reader.parse(text)
        self.assertFalse(cases[1]["passed"])
        self.assertEqual({k for k,v in cases[1]["checks"].items() if not v},{"exact_esr"})
    def test_real_omission_negatives_detected(self):
        for variant in ("omit-enable","omit-code-mapping"):
            with self.subTest(variant=variant):
                self.assertTrue(reader.negative_detected(reader.parse(self.load(variant)),variant))
    def test_extra_negative_control_failure_rejected(self):
        for variant in ("omit-enable","omit-code-mapping"):
            with self.subTest(variant=variant):
                text=self.load(variant)
                prefix="g4096_success.tcr "
                row=next(x for x in text.splitlines() if x.startswith(prefix))
                changed=prefix+f"{int(row.split()[1],16)^1:016x} "
                cases=reader.parse(text.replace(row,changed,1))
                self.assertFalse(reader.negative_detected(cases,variant))
    def test_unrelated_negative_case_failure_rejected(self):
        for variant in ("omit-enable","omit-code-mapping"):
            with self.subTest(variant=variant):
                text=self.load(variant).replace("g4096_data_unmapped 0000000096000007",
                                               "g4096_data_unmapped 0000000096000006",1)
                self.assertFalse(reader.negative_detected(reader.parse(text),variant))
if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--oracle-run",type=Path,required=True)
    args=ap.parse_args();CAPTURE=args.oracle_run.resolve()
    unittest.main(argv=[__file__],verbosity=2)
