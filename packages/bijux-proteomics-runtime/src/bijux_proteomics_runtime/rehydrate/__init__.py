"""Completed-run rehydration surfaces."""

from __future__ import annotations

from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.support.primitives.stability import sealed

__all__ = ["load_completed_run"]

sealed()
