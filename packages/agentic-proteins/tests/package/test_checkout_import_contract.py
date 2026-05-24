# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def test_agentic_root_import_succeeds_from_clean_checkout() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import agentic_proteins"],
        capture_output=True,
        text=True,
        cwd=_repository_root(),
        env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        check=False,
    )

    assert result.returncode == 0, result.stderr
