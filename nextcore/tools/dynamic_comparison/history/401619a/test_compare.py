#!/usr/bin/env python3
"""Bounded comparator regressions; reads frozen evidence and mutates copies only."""
from pathlib import Path
import argparse,copy,json,struct,unittest
import compare as c

class ComparisonTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.arm={x["name"]:x for x in json.loads((ORACLE/"captured/report.json").read_text())["cases"]}
  cls.native=json.loads((EVIDENCE/"receipt.json").read_text())["cases"]
 def evaluate(self,index=0,change=None):
  row=self.native[index];arm=copy.deepcopy(self.arm[row["name"]]);native=copy.deepcopy(row["actual"])
  ram=(EVIDENCE/(row["name"]+".ram-after.bin")).read_bytes()
  expected=bytearray((EVIDENCE/(row["name"]+".ram-before.bin")).read_bytes())
  # Original ELF/captured input geometry, not runtime-generated values.
  struct.pack_into("<QQ",expected,0xc000,arm["observed_input"]["data_after0"],arm["observed_input"]["data_after1"])
  if change:change(arm,native,expected)
  return c.compare(arm,native,ram,expected)
 def test_all_six_frozen_cases(self):
  self.assertEqual(len(self.native),6)
  for i in range(6):
   with self.subTest(case=i):self.assertTrue(self.evaluate(i)["passed"])
 def test_changed_expected_esr(self):
  i=next(i for i,x in enumerate(self.native) if x["name"]=="g4096_fetch_unmapped")
  def change(a,n,r):a["observed"]["esr"]^=1
  got=self.evaluate(i,change)
  self.assertEqual({k for k,v in got["checks"].items() if not v},{"guest_esr","reply_esr"})
 def test_success_cannot_retire_hvc(self):
  def change(a,n,r):n["cpu"][33]+=1
  self.assertFalse(self.evaluate(change=change)["checks"]["authored_retirement_boundary"])
 def test_false_success_or_system_trap_rejected(self):
  for status in (0,13):
   def change(a,n,r):n["result"]["status"]=status;n["cpu"][47]=status
   self.assertFalse(self.evaluate(change=change)["checks"]["native_boundary_status"])
 def test_changed_pc_rejected(self):
  def change(a,n,r):n["cpu"][32]+=4
  self.assertFalse(self.evaluate(change=change)["checks"]["original_pc_boundary"])
 def test_changed_hvc_fetch_rejected(self):
  def change(a,n,r):n["result"]["reply_value0"]=0xd503201f
  self.assertFalse(self.evaluate(change=change)["checks"]["unaltered_hvc_fetched"])
 def test_changed_loaded_witness_rejected(self):
  def change(a,n,r):n["cpu"][12]^=1
  self.assertFalse(self.evaluate(change=change)["checks"]["captured_loaded_value"])
 def test_changed_backing_expectation_rejected(self):
  def change(a,n,r):r[0xc000]^=1
  self.assertFalse(self.evaluate(change=change)["checks"]["native_full_backing_authored_effect"])
 def test_missing_real_callback_rejected(self):
  def change(a,n,r):n["result"]["data_requests"]=0
  self.assertFalse(self.evaluate(change=change)["checks"]["native_callback_counts"])
 def test_missing_compiled_blocks_rejected(self):
  def change(a,n,r):n["cpu"][45]=0
  self.assertFalse(self.evaluate(change=change)["checks"]["native_compiled_blocks"])
 def test_native_unsupported_bookkeeping_rejected(self):
  def change(a,n,r):n["cpu"][38]=0
  self.assertFalse(self.evaluate(change=change)["checks"]["native_unsupported_bookkeeping"])
 def test_duplicate_native_record_rejected(self):
  with self.assertRaises(ValueError):c.load_observed("CPU a 0\nCPU a 0\n")
 def test_historical_missing_instruction_length_rejected(self):
  def change(a,n,r):n["cpu"][36]=0
  self.assertFalse(self.evaluate(change=change)["checks"]["native_unsupported_bookkeeping"])
 def test_unexpected_native_record_rejected(self):
  with self.assertRaises(ValueError):c.load_observed("PASS a 0\n")

if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--oracle",type=Path,required=True);p.add_argument("--evidence",type=Path,required=True)
 a=p.parse_args();ORACLE=a.oracle;EVIDENCE=a.evidence
 unittest.main(argv=[__file__],verbosity=2)
