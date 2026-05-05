"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runs.logging import (
    NoopStructuredLogger,
    StructuredLogger,
)

__all__ = ["NoopStructuredLogger", "StructuredLogger"]
