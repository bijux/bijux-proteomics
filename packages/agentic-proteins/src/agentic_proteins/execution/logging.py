"""Legacy execution alias for orchestration logging helpers."""

from bijux_proteomics_runtime.runs.logging import (
    NoopStructuredLogger,
    StructuredLogger,
)

__all__ = ["NoopStructuredLogger", "StructuredLogger"]
