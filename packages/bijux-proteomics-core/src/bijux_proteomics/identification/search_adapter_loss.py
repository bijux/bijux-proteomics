# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific loss and disagreement surfaces for search-adapter normalization."""

from __future__ import annotations

from itertools import combinations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.confidence import (
    compare_protein_inference_strategies,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterConformanceReport,
    SearchAdapterFieldAccounting,
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchResultFamily,
    build_search_adapter_conformance_report,
    build_search_adapter_field_accounting,
)
from bijux_proteomics_foundation import JsonModel


class SearchAdapterInformationLossReport(JsonModel):
    """Material-loss accounting for one adapter normalization surface."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    result_family: SearchResultFamily
    field_accounting: SearchAdapterFieldAccounting
    material_lost_columns: tuple[str, ...] = Field(default_factory=tuple)
    acceptable_for_identification_claims: bool
    acceptability_note: str = Field(..., min_length=1)


class ProteinInferenceDisagreementEntry(JsonModel):
    """One protein-inference disagreement between two engine normalizations."""

    model_config = ConfigDict(extra="forbid")

    left_adapter_kind: SearchAdapterKind
    right_adapter_kind: SearchAdapterKind
    strategy_label: str = Field(..., min_length=1)
    shared_proteins: tuple[str, ...] = Field(default_factory=tuple)
    left_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    right_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    jaccard_similarity: float = Field(..., ge=0.0, le=1.0)
    material: bool


class ProteinInferenceEngineDisagreementDossier(JsonModel):
    """Cross-engine dossier for protein-inference disagreement after normalization."""

    model_config = ConfigDict(extra="forbid")

    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    entries: tuple[ProteinInferenceDisagreementEntry, ...] = Field(
        default_factory=tuple
    )
    material_disagreement_count: int = Field(..., ge=0)


class SearchAdapterParityCheck(JsonModel):
    """One release-relevant parity criterion over adapter normalization."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    passed: bool
    detail: str = Field(..., min_length=1)


class SearchAdapterParityReport(JsonModel):
    """Serious acceptance criteria for adapter parity and release claims."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    result_family: SearchResultFamily
    information_loss: SearchAdapterInformationLossReport
    conformance: SearchAdapterConformanceReport
    checks: tuple[SearchAdapterParityCheck, ...] = Field(default_factory=tuple)
    release_acceptable: bool
    failing_criteria: tuple[str, ...] = Field(default_factory=tuple)


def _material_columns(report: SearchAdapterNormalizationReport) -> set[str]:
    mapping = report.adapter_manifest.mapping
    if mapping is None:
        return set()
    fields = {
        mapping.spectrum_id,
        mapping.peptide,
        mapping.score,
        mapping.protein_refs,
        mapping.q_value,
        mapping.decoy_label,
    }
    return {field for field in fields if field}


def build_search_adapter_information_loss_report(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterInformationLossReport:
    """State whether normalization preserved the fields needed for identification claims."""

    field_accounting = build_search_adapter_field_accounting(normalization_report)
    material_lost_columns = tuple(
        sorted(
            set(field_accounting.lost_columns) & _material_columns(normalization_report)
        )
    )
    acceptable = not material_lost_columns
    return SearchAdapterInformationLossReport(
        adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        result_family=normalization_report.adapter_manifest.result_family,
        field_accounting=field_accounting,
        material_lost_columns=material_lost_columns,
        acceptable_for_identification_claims=acceptable,
        acceptability_note=(
            "normalization preserved the protein, score, and decoy fields needed for identification claims"
            if acceptable
            else "normalization dropped one or more material fields needed for identification claims"
        ),
    )


def build_protein_inference_engine_disagreement_dossier(
    reports: tuple[SearchAdapterNormalizationReport, ...],
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceEngineDisagreementDossier:
    """Compare protein-inference selections across multiple engine-normalized reports."""

    entries: list[ProteinInferenceDisagreementEntry] = []
    for left_report, right_report in combinations(reports, 2):
        left_comparison = compare_protein_inference_strategies(
            left_report.normalized_records,
            picked_threshold=picked_threshold,
        )
        right_comparison = compare_protein_inference_strategies(
            right_report.normalized_records,
            picked_threshold=picked_threshold,
        )
        left_by_label = {
            entry.strategy_label: set(entry.selected_proteins)
            for entry in left_comparison.selections
        }
        right_by_label = {
            entry.strategy_label: set(entry.selected_proteins)
            for entry in right_comparison.selections
        }
        shared_labels = sorted(set(left_by_label) & set(right_by_label))
        for strategy_label in shared_labels:
            left_selected = left_by_label[strategy_label]
            right_selected = right_by_label[strategy_label]
            union = left_selected | right_selected
            intersection = left_selected & right_selected
            similarity = len(intersection) / len(union) if union else 1.0
            entries.append(
                ProteinInferenceDisagreementEntry(
                    left_adapter_kind=left_report.adapter_manifest.adapter_kind,
                    right_adapter_kind=right_report.adapter_manifest.adapter_kind,
                    strategy_label=strategy_label,
                    shared_proteins=tuple(sorted(intersection)),
                    left_only_proteins=tuple(sorted(left_selected - right_selected)),
                    right_only_proteins=tuple(sorted(right_selected - left_selected)),
                    jaccard_similarity=similarity,
                    material=similarity < 1.0,
                )
            )
    return ProteinInferenceEngineDisagreementDossier(
        adapter_kinds=tuple(report.adapter_manifest.adapter_kind for report in reports),
        entries=tuple(entries),
        material_disagreement_count=sum(1 for entry in entries if entry.material),
    )


def build_search_adapter_parity_report(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterParityReport:
    """Evaluate whether a normalized adapter surface meets serious parity criteria."""

    information_loss = build_search_adapter_information_loss_report(
        normalization_report
    )
    conformance = build_search_adapter_conformance_report(normalization_report)
    field_roles = set(information_loss.field_accounting.mapped_field_roles)
    checks = (
        SearchAdapterParityCheck(
            code="imported_semantics",
            passed=(
                len(normalization_report.normalized_records) > 0
                and {"spectrum_id", "peptide", "charge", "score"} <= field_roles
            ),
            detail=(
                "normalized output preserves spectrum identity, peptide identity, charge, and comparable score semantics"
            ),
        ),
        SearchAdapterParityCheck(
            code="loss_accounting",
            passed=information_loss.acceptable_for_identification_claims,
            detail=(
                "field accounting discloses adapter loss and no material identification columns are missing"
            ),
        ),
        SearchAdapterParityCheck(
            code="confidence_normalization",
            passed=(
                conformance.fdr_audit_trail is not None
                and conformance.calibration_plot is not None
                and conformance.passes
            ),
            detail=(
                "adapter parity requires conformance, FDR audit output, and calibration evidence instead of raw score import only"
            ),
        ),
        SearchAdapterParityCheck(
            code="failure_disclosure",
            passed=(
                conformance.rejected_rows == 0
                or bool(conformance.rejection_issue_counts)
            ),
            detail=(
                "adapter parity requires machine-readable disclosure for rejected rows and malformed inputs"
            ),
        ),
    )
    failing_criteria = tuple(check.code for check in checks if not check.passed)
    return SearchAdapterParityReport(
        adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        result_family=normalization_report.adapter_manifest.result_family,
        information_loss=information_loss,
        conformance=conformance,
        checks=checks,
        release_acceptable=not failing_criteria,
        failing_criteria=failing_criteria,
    )
