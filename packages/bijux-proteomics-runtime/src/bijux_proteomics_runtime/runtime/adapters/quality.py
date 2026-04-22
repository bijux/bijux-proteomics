"""Runtime adapters for intelligence quality semantics."""

from __future__ import annotations

from bijux_proteomics_intelligence.domain.metrics.quality import MetricValue, QCStatus, ToolReliability


def qc_status_value(status: QCStatus) -> str:
    """Return stable QC status value for runtime artifacts."""
    return status.value


__all__ = ["MetricValue", "QCStatus", "ToolReliability", "qc_status_value"]
