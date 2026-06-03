from __future__ import annotations

# ruff: noqa: E402, I001

import sys
import unittest
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src"))

pytestmark = pytest.mark.unit

from bijux_proteomics_foundation import DocumentSchema as RuntimeDocumentSchema
from proteomics_foundation import DocumentSchema, __version__


class ProteomicsFoundationCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_foundation_symbols(self) -> None:
        self.assertIs(DocumentSchema, RuntimeDocumentSchema)
        self.assertIsInstance(__version__, str)


if __name__ == "__main__":
    unittest.main()
