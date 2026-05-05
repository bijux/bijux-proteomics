"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runtime.context.telemetry import (
    TelemetryClient,
    TelemetrySample,
)

__all__ = ["TelemetryClient", "TelemetrySample"]
