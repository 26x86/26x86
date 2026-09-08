# Host gate validation

Executed under Ubuntu 24.04 / Python 3:

```sh
python3 -m unittest discover -s nextcore/tools -p test_verify_apfs_jumpstart.py -v
```

Final observed result: **9 tests passed, 0 failures**, 0.018 seconds. This note
records the captured tool result; it is not substituted raw subprocess output.
Tests cover PE copy scope, noncontiguous extents and final padding, independent
checksum residues/corruption, both GPT CRCs, all six expected marker sequences,
missing/duplicate/reordered evidence, wrong count/readback/result, unexpected
default child entry, abnormal exit and surviving children, and atomic receipt
availability after deadline/I/O failures during post-hashing.
