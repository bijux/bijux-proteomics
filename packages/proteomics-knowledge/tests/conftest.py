# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.pytest_artifacts import (
    configure_hypothesis_artifacts,
)

ROOT = Path(__file__).resolve().parents[3]
configure_hypothesis_artifacts(ROOT)
