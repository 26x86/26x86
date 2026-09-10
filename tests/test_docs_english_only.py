#!/usr/bin/env python3
"""
Test suite to enforce the English-only documentation policy across 26x86 / NextCore.
Scans docs/ and root markdown files to verify zero non-English / Korean characters.
"""

import os
import re
import sys
import unittest

HANGUL_PATTERN = re.compile(r'[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]')

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


class TestDocumentationEnglishOnly(unittest.TestCase):
    def test_docs_directory_is_english_only(self):
        """Verify that all markdown files in docs/ contain zero Korean characters."""
        violations = []
        for dirpath, dirnames, filenames in os.walk(DOCS_DIR):
            for filename in filenames:
                if not filename.endswith(".md"):
                    continue
                filepath = os.path.join(dirpath, filename)
                relpath = os.path.relpath(filepath, REPO_ROOT)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        matches = HANGUL_PATTERN.findall(line)
                        if matches:
                            violations.append(
                                f"{relpath}:{line_num}: found non-English characters {matches} in line: {line.strip()[:80]}"
                            )
        
        self.assertEqual(
            violations,
            [],
            "Non-English text detected in docs/ directory:\n" + "\n".join(violations),
        )

    def test_root_markdown_files_are_english_only(self):
        """Verify that all markdown files at repository root contain zero Korean characters."""
        violations = []
        for filename in os.listdir(REPO_ROOT):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(REPO_ROOT, filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    matches = HANGUL_PATTERN.findall(line)
                    if matches:
                        violations.append(
                            f"{filename}:{line_num}: found non-English characters {matches} in line: {line.strip()[:80]}"
                        )
        
        self.assertEqual(
            violations,
            [],
            "Non-English text detected in root markdown files:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestDocumentationEnglishOnly)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
