# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional scientific export for evidence-aware biological ranking outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    render_evidence_aware_ranking_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalRankingExportNames:
    """Artifact names emitted for optional evidence-aware ranking outputs."""

    evidence_aware_ranking_name: str | None


def _write_biological_optional_ranking_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalRankingExportNames:
    evidence_aware_ranking_name = None
    if report.evidence_aware_ranking_report is not None:
        evidence_aware_ranking_name = "biological_evidence_aware_ranking.tsv"
        write_output_table_tsv(
            output_dir / evidence_aware_ranking_name,
            render_evidence_aware_ranking_tsv(report.evidence_aware_ranking_report),
        )
    return BiologicalRankingExportNames(
        evidence_aware_ranking_name=evidence_aware_ranking_name
    )


__all__ = [
    "BiologicalRankingExportNames",
    "_write_biological_optional_ranking_exports",
]
