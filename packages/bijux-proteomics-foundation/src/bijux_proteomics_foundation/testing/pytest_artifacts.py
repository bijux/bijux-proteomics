# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared pytest artifact bootstrap helpers for repository package suites."""

from __future__ import annotations

import os
from pathlib import Path

from hypothesis.configuration import set_hypothesis_home_dir


def configure_hypothesis_artifacts(repository_root: Path) -> None:
    """Keep Hypothesis state inside the governed repository artifact root."""

    hypothesis_root = repository_root / "artifacts" / "root" / "hypothesis"
    hypothesis_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(hypothesis_root))
    set_hypothesis_home_dir(hypothesis_root)
