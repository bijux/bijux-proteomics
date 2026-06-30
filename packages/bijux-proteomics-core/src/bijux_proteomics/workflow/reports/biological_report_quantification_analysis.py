# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned quantification preparation for biological report assembly."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
)
from bijux_proteomics.quantification.normalization import (
    normalize_label_free_table,
)
from bijux_proteomics.quantification.statistics import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
)
from bijux_proteomics.study import ExperimentDesign
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _resolve_contrast,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultSelectionPolicy,
    _resolve_biological_result_selection_policy,
)


class BiologicalQuantificationAnalysis(NamedTuple):
    """Normalized quantification inputs and governed differential outputs."""

    design_entries: tuple[ExperimentalDesignEntry, ...]
    selection_policy: BiologicalResultSelectionPolicy
    normalized_table: LabelFreeQuantTable
    resolved_condition_a: str
    resolved_condition_b: str
    differential_report: DifferentialAbundanceReport


def _build_biological_quantification_analysis(
    quant_table: LabelFreeQuantTable,
    experiment_design: ExperimentDesign,
    *,
    normalization_method: NormalizationMethod,
    condition_a: str | None,
    condition_b: str | None,
    selection_policy: BiologicalResultSelectionPolicy | None,
    protocol_context_tsv_path: Path | None,
) -> BiologicalQuantificationAnalysis:
    design_entries = experiment_design.entries
    active_selection_policy = _resolve_biological_result_selection_policy(
        selection_policy,
        protocol_context_tsv_path=protocol_context_tsv_path,
    )
    normalized_table = normalize_label_free_table(
        quant_table,
        method=normalization_method,
    )
    if normalized_table.entity_level != QuantEntityLevel.PROTEIN:
        raise ValueError(
            "biological result reporting requires a protein-level quantification table"
        )
    if normalized_table.measure_kind != QuantMeasureKind.INTENSITY:
        raise ValueError(
            "biological result reporting requires intensity-based protein quantification"
        )
    resolved_condition_a, resolved_condition_b = _resolve_contrast(
        design_entries,
        condition_a=condition_a,
        condition_b=condition_b,
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            normalized_table,
            design_entries,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    return BiologicalQuantificationAnalysis(
        design_entries=design_entries,
        selection_policy=active_selection_policy,
        normalized_table=normalized_table,
        resolved_condition_a=resolved_condition_a,
        resolved_condition_b=resolved_condition_b,
        differential_report=differential_report,
    )
