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
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "bijux-proteomics-core" / "src"))

from bijux_proteomics import DigestPolicy as RuntimeDigestPolicy
from bijux_proteomics.sequences import parse_fasta_document as runtime_parse_fasta
from proteomics import DigestPolicy, __version__
from proteomics.cli import main

parse_fasta_document = cast(
    Any,
    import_module("proteomics.sequences"),
).parse_fasta_document


class ProteomicsCompatibilityTests(unittest.TestCase):
    def test_alias_root_re_exports_core_symbols(self) -> None:
        self.assertIs(DigestPolicy, RuntimeDigestPolicy)
        self.assertIsInstance(__version__, str)

    def test_alias_submodules_keep_canonical_identity(self) -> None:
        self.assertIs(parse_fasta_document, runtime_parse_fasta)

    def test_cli_entrypoint_is_exposed(self) -> None:
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
