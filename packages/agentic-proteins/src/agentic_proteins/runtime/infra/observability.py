"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runtime.context.logging import (
    NoopStructuredLogger,
    StructuredLogger,
)

__all__ = ["NoopStructuredLogger", "StructuredLogger"]
