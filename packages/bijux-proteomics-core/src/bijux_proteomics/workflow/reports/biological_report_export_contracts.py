# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Manifest contracts for exported biological report bundles."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.reports.biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)
from bijux_proteomics.workflow.reports.biological_report_summary_contracts import (
    BiologicalResultReportSummary,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultReportExportManifest(JsonModel):
    """Stable manifest over one exported biological result report directory."""

    model_config = ConfigDict(extra="forbid")

    summary: BiologicalResultReportSummary
    artifacts: BiologicalResultReportArtifactPaths
    claim_validation_included: bool
    hypothesis_summary_included: bool
    context_summary_included: bool
    cohort_stratification_summary_included: bool
    tissue_context_summary_included: bool
    drug_target_summary_included: bool
    disease_phenotype_summary_included: bool
    go_summary_included: bool
    pathway_summary_included: bool
    complex_summary_included: bool
    note: str = Field(..., min_length=1)


__all__ = ["BiologicalResultReportExportManifest"]
