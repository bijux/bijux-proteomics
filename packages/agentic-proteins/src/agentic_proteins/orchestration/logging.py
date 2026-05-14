"""Compatibility run-logging entrypoints."""

from bijux_proteomics_runtime.runs.logging import (
    NoopStructuredLogger,
    StructuredLogger,
)

__all__ = ["NoopStructuredLogger", "StructuredLogger"]
