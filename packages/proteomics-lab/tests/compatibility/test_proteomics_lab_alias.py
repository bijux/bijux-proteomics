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
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src"))

from bijux_proteomics_lab import (
    plan_experiment_batches as runtime_plan_experiment_batches,
)
from proteomics_lab import __version__, plan_experiment_batches


class ProteomicsLabCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_lab_symbols(self) -> None:
        self.assertIs(plan_experiment_batches, runtime_plan_experiment_batches)
        self.assertIsInstance(__version__, str)


if __name__ == "__main__":
    unittest.main()
