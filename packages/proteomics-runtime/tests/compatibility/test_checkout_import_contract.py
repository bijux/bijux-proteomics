from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_proteomics_runtime_cli_import_succeeds_from_clean_checkout() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "from proteomics_runtime.cli import main"],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        check=False,
    )

    assert result.returncode == 0, result.stderr
