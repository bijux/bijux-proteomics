# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import os
from pathlib import Path

from hypothesis.configuration import set_hypothesis_home_dir

_REPOSITORY_ROOT = Path(__file__).resolve().parent
_HYPOTHESIS_ROOT = _REPOSITORY_ROOT / "artifacts" / "root" / "hypothesis"


def pytest_configure() -> None:
    """Keep Hypothesis state inside repository artifacts for all local pytest runs."""

    _HYPOTHESIS_ROOT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(_HYPOTHESIS_ROOT))
    set_hypothesis_home_dir(_HYPOTHESIS_ROOT)
