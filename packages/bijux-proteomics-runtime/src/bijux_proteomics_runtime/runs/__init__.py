"""Run-owned execution surfaces and typed run contracts."""

from __future__ import annotations

from bijux_proteomics_runtime.support.primitives.stability import sealed
from bijux_proteomics_runtime.runs.public import __all__, __getattr__

sealed()
