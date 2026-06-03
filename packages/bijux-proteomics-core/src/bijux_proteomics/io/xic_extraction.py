# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401,F403

"""Compatibility facade for canonical XIC target, trace, and mzML extraction owners."""

from __future__ import annotations

from bijux_proteomics.io.chromatography.xic import *
from bijux_proteomics.io.raw.xic_extraction import (
    extract_mzml_xic_traces as extract_mzml_xic_traces,
)
from bijux_proteomics.io.tables.xic_target_table import *
