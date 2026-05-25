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
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-knowledge" / "src"))

from bijux_proteomics_knowledge import EvidenceBundle as RuntimeEvidenceBundle
from proteomics_knowledge import EvidenceBundle, __version__


class ProteomicsKnowledgeCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_knowledge_symbols(self) -> None:
        self.assertIs(EvidenceBundle, RuntimeEvidenceBundle)
        self.assertIsInstance(__version__, str)


if __name__ == "__main__":
    unittest.main()
