from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_runtime_imports_succeed_without_optional_provider_dependencies() -> None:
    pythonpath = ":".join(
        [
            str(REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-core" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-knowledge" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-intelligence" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src"),
            str(REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "src"),
        ]
    )
    script = """
import importlib.abc
import os
import sys


class BlockOptionalImports(importlib.abc.MetaPathFinder):
    def __init__(self, blocked):
        self._blocked = blocked

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in self._blocked:
            raise ModuleNotFoundError(fullname)
        return None


blocked = {
    "torch",
    "transformers",
    "einops",
    "openprotein",
    "colabfold",
    "langchain_core",
    "langchain_community",
    "langchain_huggingface",
    "langchain_text_splitters",
    "langsmith",
}
sys.meta_path.insert(0, BlockOptionalImports(blocked))
sys.path[:] = os.environ["PYTHONPATH"].split(":") + sys.path

import bijux_proteomics_runtime
from bijux_proteomics_runtime.api.cli import cli
from bijux_proteomics_runtime.providers.catalog import provider_metadata

metadata = provider_metadata()

assert bijux_proteomics_runtime.__all__
assert cli is not None
assert "heuristic_proxy" in metadata
assert "local_esmfold" not in metadata
assert "local_rosettafold" not in metadata
assert "api_colabfold" in metadata
assert "api_openprotein_esmfold" in metadata
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": pythonpath,
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
