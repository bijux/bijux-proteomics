from __future__ import annotations

# ruff: noqa: E402, I001

import sys
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(
    0, str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src")
)
sys.path.insert(
    0, str(REPO_ROOT / "packages" / "bijux-proteomics-intelligence" / "src")
)

from bijux_proteomics_intelligence import candidates as runtime_candidates
from proteomics_intelligence import __version__, candidates


class ProteomicsIntelligenceCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_intelligence_symbols(self) -> None:
        self.assertIs(candidates, runtime_candidates)
        self.assertIsInstance(__version__, str)


if __name__ == "__main__":
    unittest.main()
