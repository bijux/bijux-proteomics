from __future__ import annotations

# ruff: noqa: E402, I001

from importlib import import_module
import sys
import unittest
from pathlib import Path
from typing import Any, cast

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(
    0, str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src")
)
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-core" / "src"))

from bijux_proteomics.io.formats import (
    parse_experimental_design_table as runtime_parse_design,
)
from proteomics_core import build_normalized_run_bundle, __version__

parse_experimental_design_table = cast(
    Any,
    import_module("proteomics_core.io.formats"),
).parse_experimental_design_table


class ProteomicsCoreCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_core_symbols(self) -> None:
        self.assertTrue(callable(build_normalized_run_bundle))
        self.assertIsInstance(__version__, str)

    def test_alias_submodules_keep_canonical_identity(self) -> None:
        self.assertIs(parse_experimental_design_table, runtime_parse_design)


if __name__ == "__main__":
    unittest.main()
