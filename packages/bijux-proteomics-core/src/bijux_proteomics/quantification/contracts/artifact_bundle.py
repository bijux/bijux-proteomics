# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    pass


from .design import QuantDesignMatrixReport, QuantDesignModelFitReport
from .differential import (
    DifferentialAbundanceReport,
    MultiConditionDifferentialAbundanceReport,
    TimeCourseDifferentialReport,
)
from .input_models import (
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from .matrix_building import build_quant_matrix_export
from .matrix_models import LabelFreeQuantTable, QuantMatrixExport
from .missingness import (
    MissingDataMechanismReport,
    MissingnessConditionSummaryReport,
    MissingnessEntitySummaryReport,
    MissingnessIntensityDependenceReport,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    summarize_missing_values,
)
from .normalization_imputation import (
    ImputationReport,
    ImputationSensitivityReport,
    NormalizationComparisonReport,
    NormalizationStrategyComparisonReport,
)
from .study_qc import ReplicateAndBatchQcReport

_STABLE_DOCUMENT_TIME = datetime(1970, 1, 1, tzinfo=UTC)


class QuantReproducibilityManifest(JsonModel):
    """Stable manifest proving one quant table can be reproduced exactly."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    value_count: int = Field(..., ge=0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


class QuantArtifactBundle(JsonModel):
    """Review-ready quantification artifact bundle independent of runtime logs."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    matrix_export: QuantMatrixExport
    missing_value_summary: MissingValueSummaryReport
    imputation_report: ImputationReport | None = None
    imputation_sensitivity_report: ImputationSensitivityReport | None = None
    missingness_entity_summary: MissingnessEntitySummaryReport | None = None
    missingness_condition_summary: MissingnessConditionSummaryReport | None = None
    missingness_intensity_dependence: MissingnessIntensityDependenceReport | None = None
    missingness_mechanism_report: MissingDataMechanismReport | None = None
    replicate_qc_report: ReplicateAndBatchQcReport | None = None
    reproducibility_manifest: QuantReproducibilityManifest
    normalization_comparison_report: NormalizationComparisonReport | None = None
    normalization_strategy_report: NormalizationStrategyComparisonReport | None = None
    limma_compatible_package: object | None = None
    msstats_compatible_input_report: object | None = None
    design_matrix_report: QuantDesignMatrixReport | None = None
    design_model_fit_report: QuantDesignModelFitReport | None = None
    differential_abundance_report: DifferentialAbundanceReport | None = None
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None
    time_course_differential_report: TimeCourseDifferentialReport | None = None


def build_quant_reproducibility_manifest(
    table: LabelFreeQuantTable,
) -> QuantReproducibilityManifest:
    """Build a stable reproducibility manifest for one quantification table."""
    payload = [
        table.entity_level.value,
        table.measure_kind.value,
        table.aggregation_method.value,
        table.normalization_method.value,
        tuple(table.sample_ids),
        tuple(table.entity_ids),
        tuple(sorted(table.normalization_factors.items())),
        tuple(
            (
                value.entity_id,
                value.sample_id,
                value.abundance,
                value.missing_value_kind.value,
                value.source_feature_count,
                None
                if value.value_provenance is None
                else (
                    value.value_provenance.aggregation_method.value,
                    value.value_provenance.value_origin.value,
                    tuple(value.value_provenance.source_feature_ids),
                    tuple(value.value_provenance.source_peptides),
                    tuple(value.value_provenance.source_precursor_ids),
                    tuple(
                        (
                            contributor.contributor_id,
                            contributor.contributor_kind.value,
                            contributor.canonical_peptide,
                            tuple(contributor.protein_refs),
                            contributor.abundance,
                            contributor.missing_value_kind.value,
                        )
                        for contributor in value.value_provenance.selected_contributors
                    ),
                    tuple(
                        (
                            excluded.contributor.contributor_id,
                            excluded.contributor.contributor_kind.value,
                            excluded.reason_code,
                        )
                        for excluded in value.value_provenance.excluded_contributors
                    ),
                ),
                None
                if value.imputation_provenance is None
                else (
                    value.imputation_provenance.method.value,
                    value.imputation_provenance.original_missing_value_kind.value,
                    value.imputation_provenance.strategy,
                    value.imputation_provenance.reference_group,
                    tuple(value.imputation_provenance.donor_sample_ids),
                    tuple(value.imputation_provenance.donor_entity_ids),
                ),
            )
            for value in sorted(
                table.values,
                key=lambda entry: (entry.entity_id, entry.sample_id),
            )
        ),
    ]
    reproducibility_hash = hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()
    manifest = QuantReproducibilityManifest(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="quant_reproducibility_manifest",
            package_name="bijux-proteomics-core",
            status="generated",
            created_at=_STABLE_DOCUMENT_TIME,
            updated_at=_STABLE_DOCUMENT_TIME,
        ),
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        normalization_method=table.normalization_method,
        sample_ids=table.sample_ids,
        entity_ids=table.entity_ids,
        value_count=len(table.values),
        reproducibility_hash=reproducibility_hash,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def export_quant_reproducibility_manifest(
    manifest: QuantReproducibilityManifest,
    path: Path,
) -> None:
    """Write a stable JSON reproducibility manifest for quantification outputs."""
    path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")


def build_quant_artifact_bundle(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    missing_value_policy: MissingValueSummaryPolicy | None = None,
    imputation_report: ImputationReport | None = None,
    imputation_sensitivity_report: ImputationSensitivityReport | None = None,
    missingness_entity_summary: MissingnessEntitySummaryReport | None = None,
    missingness_condition_summary: MissingnessConditionSummaryReport | None = None,
    missingness_intensity_dependence: MissingnessIntensityDependenceReport
    | None = None,
    missingness_mechanism_report: MissingDataMechanismReport | None = None,
    replicate_qc_report: ReplicateAndBatchQcReport | None = None,
    normalization_comparison_report: NormalizationComparisonReport | None = None,
    normalization_strategy_report: NormalizationStrategyComparisonReport | None = None,
    limma_compatible_package: object | None = None,
    msstats_compatible_input_report: object | None = None,
    design_matrix_report: QuantDesignMatrixReport | None = None,
    design_model_fit_report: QuantDesignModelFitReport | None = None,
    differential_abundance_report: DifferentialAbundanceReport | None = None,
    differential_abundance_multi_condition_report: (
        MultiConditionDifferentialAbundanceReport | None
    ) = None,
    time_course_differential_report: TimeCourseDifferentialReport | None = None,
) -> QuantArtifactBundle:
    """Bundle quant outputs so review can happen without workflow runtime logs."""
    bundle = QuantArtifactBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="quant_artifact_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
            created_at=_STABLE_DOCUMENT_TIME,
            updated_at=_STABLE_DOCUMENT_TIME,
        ),
        matrix_export=build_quant_matrix_export(table, design_entries=design_entries),
        missing_value_summary=summarize_missing_values(
            table,
            policy=missing_value_policy,
        ),
        imputation_report=imputation_report,
        imputation_sensitivity_report=imputation_sensitivity_report,
        missingness_entity_summary=missingness_entity_summary,
        missingness_condition_summary=missingness_condition_summary,
        missingness_intensity_dependence=missingness_intensity_dependence,
        missingness_mechanism_report=missingness_mechanism_report,
        replicate_qc_report=replicate_qc_report,
        reproducibility_manifest=build_quant_reproducibility_manifest(table),
        normalization_comparison_report=normalization_comparison_report,
        normalization_strategy_report=normalization_strategy_report,
        limma_compatible_package=limma_compatible_package,
        msstats_compatible_input_report=msstats_compatible_input_report,
        design_matrix_report=design_matrix_report,
        design_model_fit_report=design_model_fit_report,
        differential_abundance_report=differential_abundance_report,
        differential_abundance_multi_condition_report=(
            differential_abundance_multi_condition_report
        ),
        time_course_differential_report=time_course_differential_report,
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def write_quant_artifact_bundle(bundle: QuantArtifactBundle, path: Path) -> None:
    """Write a stable JSON artifact bundle for quant review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def export_quant_artifact_bundle(bundle: QuantArtifactBundle, path: Path) -> None:
    """Compatibility wrapper for the legacy quant artifact bundle export name."""

    write_quant_artifact_bundle(bundle, path)
