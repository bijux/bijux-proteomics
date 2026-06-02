from __future__ import annotations

# ruff: noqa: E402, I001

import sys
import unittest
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(
    0, str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src")
)
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "src"))

pytestmark = pytest.mark.unit

from bijux_proteomics_runtime.runs.manager import RunManager as RuntimeRunManager
from proteomics_runtime import RunManager, __version__
from proteomics_runtime.cli import main


class ProteomicsRuntimeCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_runtime_symbols(self) -> None:
        self.assertIs(RunManager, RuntimeRunManager)
        self.assertIsInstance(__version__, str)

    def test_cli_entrypoint_is_exposed(self) -> None:
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
