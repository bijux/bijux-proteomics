# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401

"""Click choice factories for sequence-adjacent interface commands."""

from __future__ import annotations

from ..foundation import FragmentIonSeries, SearchEngineModifiedPeptideDialect, click
from ..identification import ScoreOrientation, SearchAdapterKind
from ..io_and_dia import FormatConversionTarget, WorkflowSchedulerKind
from ..multiplex_targeted import (
    SilacLabel,
    TmtNormalizationMethod,
    TmtSearchResultSourceKind,
)
from ..ptm_quantification.quantification import (
    HeatmapMissingValuePolicy,
    ImputationMethod,
    NormalizationMethod,
    PeptideMatrixGroupingMode,
    ProteinMatrixTargetKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from ..review_sequences_study import (
    DecoyGenerationMode,
    DuplicateAccessionPolicy,
    FastaParseMode,
    PeptideDigestionMode,
)


def _mode_choice() -> click.Choice[str]:
    return click.Choice([mode.value for mode in FastaParseMode], case_sensitive=False)


def _duplicate_accession_policy_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in DuplicateAccessionPolicy],
        case_sensitive=False,
    )


def _decoy_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in DecoyGenerationMode],
        case_sensitive=False,
    )


def _digestion_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideDigestionMode],
        case_sensitive=False,
    )


def _export_format_choice() -> click.Choice[str]:
    return click.Choice(["tsv", "jsonl", "parquet", "fasta"], case_sensitive=False)


def _fragment_series_choice() -> click.Choice[str]:
    return click.Choice(
        [series.value for series in FragmentIonSeries], case_sensitive=False
    )


def _modified_peptide_dialect_choice() -> click.Choice[str]:
    return click.Choice(
        [dialect.value for dialect in SearchEngineModifiedPeptideDialect],
        case_sensitive=False,
    )


def _validate_kind_choice() -> click.Choice[str]:
    return click.Choice(
        ["auto", "fasta", "psm", "mgf", "mzml", "mod-registry", "design-table"],
        case_sensitive=False,
    )


def _conversion_target_choice() -> click.Choice[str]:
    return click.Choice(
        [target.value for target in FormatConversionTarget], case_sensitive=False
    )


def _search_adapter_choice() -> click.Choice[str]:
    return click.Choice(
        [adapter.value for adapter in SearchAdapterKind], case_sensitive=False
    )


def _score_orientation_choice() -> click.Choice[str]:
    return click.Choice(
        [orientation.value for orientation in ScoreOrientation], case_sensitive=False
    )


def _quant_entity_level_choice() -> click.Choice[str]:
    return click.Choice(
        [level.value for level in QuantEntityLevel], case_sensitive=False
    )


def _quant_measure_choice() -> click.Choice[str]:
    return click.Choice(
        [measure.value for measure in QuantMeasureKind], case_sensitive=False
    )


def _quant_rollup_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in QuantRollupMethod], case_sensitive=False
    )


def _normalization_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in NormalizationMethod], case_sensitive=False
    )


def _imputation_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in ImputationMethod], case_sensitive=False
    )


def _heatmap_missing_value_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in HeatmapMissingValuePolicy],
        case_sensitive=False,
    )


def _peptide_matrix_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "psm"), case_sensitive=False)


def _peptide_matrix_builder_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "precursor", "psm"), case_sensitive=False)


def _peptide_matrix_grouping_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideMatrixGroupingMode], case_sensitive=False
    )


def _protein_matrix_target_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in ProteinMatrixTargetKind], case_sensitive=False
    )


def _tmt_source_kind_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in TmtSearchResultSourceKind], case_sensitive=False
    )


def _tmt_normalization_method_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in TmtNormalizationMethod], case_sensitive=False
    )


def _tmt_ratio_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        ("none", *[method.value for method in TmtNormalizationMethod]),
        case_sensitive=False,
    )


def _label_based_differential_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        (NormalizationMethod.NONE.value, NormalizationMethod.MEDIAN.value),
        case_sensitive=False,
    )


def _silac_label_choice() -> click.Choice[str]:
    return click.Choice([label.value for label in SilacLabel], case_sensitive=False)


def _workflow_scheduler_choice() -> click.Choice[str]:
    return click.Choice(
        [scheduler.value for scheduler in WorkflowSchedulerKind], case_sensitive=False
    )
