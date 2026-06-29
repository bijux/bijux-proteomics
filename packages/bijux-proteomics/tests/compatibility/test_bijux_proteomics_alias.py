from __future__ import annotations

# ruff: noqa: E402, I001

import sys
import unittest
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-core" / "src"))

pytestmark = pytest.mark.unit

from bijux_proteomics import DigestPolicy
from bijux_proteomics_alias import __version__


class BijuxProteomicsCompatibilityTests(unittest.TestCase):
    def test_distribution_alias_exposes_version_metadata(self) -> None:
        self.assertIsInstance(__version__, str)

    def test_distribution_alias_installs_the_canonical_core_import_root(self) -> None:
        self.assertTrue(callable(DigestPolicy))

    def test_metadata_helper_does_not_replace_the_public_core_import_root(self) -> None:
        self.assertTrue(DigestPolicy.__module__.startswith("bijux_proteomics."))
        self.assertFalse(DigestPolicy.__module__.startswith("bijux_proteomics_alias"))


if __name__ == "__main__":
    unittest.main()
