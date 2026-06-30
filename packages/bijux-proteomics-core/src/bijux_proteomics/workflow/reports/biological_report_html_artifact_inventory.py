# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report artifact inventory HTML."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_activity_artifact_inventory import (
    _build_biological_activity_artifact_sections,
)
from bijux_proteomics.workflow.reports.biological_report_html_contextual_artifact_inventory import (
    _build_biological_contextual_artifact_sections,
)
from bijux_proteomics.workflow.reports.biological_report_html_scientific_artifact_inventory import (
    _build_biological_scientific_artifact_sections,
)
from bijux_proteomics.workflow.reports.biological_report_html_visual_artifact_inventory import (
    _build_biological_visual_artifact_sections,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
)


def _render_biological_report_artifact_inventory_html(
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    sections = (
        _build_biological_scientific_artifact_sections(artifacts)
        + _build_biological_contextual_artifact_sections(artifacts)
        + _build_biological_activity_artifact_sections(artifacts)
        + _build_biological_visual_artifact_sections(artifacts)
    )
    return "".join(
        f"<li><strong>{escape(label)}</strong>: <code>{escape(path)}</code></li>"
        for label, path in sections
        if path is not None
    )


__all__ = ["_render_biological_report_artifact_inventory_html"]
