# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein parsimony inference over grouped protein evidence."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    InferenceDisagreementKind,
    ParsimonyProteinEntry,
    ParsimonyVariant,
    ParsimonyVariantComparisonReport,
    ParsimonyVariantDifferenceEntry,
    ParsimonyVariantResult,
    PsmRecord,
    TargetDecoyLabel,
    rollup_peptide_evidence,
)
from bijux_proteomics.identification.protein.protein_grouping import (
    ProteinGroupingEntry,
    build_protein_grouping_report,
)
from bijux_proteomics_foundation import JsonModel


class ProteinParsimonySummary(JsonModel):
    """Compact summary over one named protein parsimony run."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    review_variants: tuple[ParsimonyVariant, ...] = Field(default_factory=tuple)
    total_observed_peptides: int = Field(..., ge=0)
    explained_peptide_count: int = Field(..., ge=0)
    unexplained_peptide_count: int = Field(..., ge=0)
    selected_protein_count: int = Field(..., ge=0)
    shared_selected_peptide_count: int = Field(..., ge=0)
    variant_difference_count: int = Field(..., ge=0)
    unresolved_ambiguity_count: int = Field(..., ge=0)


class ProteinParsimonyProteinEntry(JsonModel):
    """One selected protein inside the named protein parsimony result."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    selection_rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    source_group_id: str = Field(..., min_length=1)
    group_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class ProteinParsimonyAmbiguityEntry(JsonModel):
    """One unresolved ambiguity left after protein parsimony selection."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(..., min_length=1)
    kind: InferenceDisagreementKind
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    strategy_assignments: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    first_difference_rank: int | None = Field(default=None, ge=1)
    note: str = Field(..., min_length=1)


class ProteinParsimonyReport(JsonModel):
    """Stable owner report over selected proteins and remaining ambiguity."""

    model_config = ConfigDict(extra="forbid")

    summary: ProteinParsimonySummary
    selected_proteins: tuple[ProteinParsimonyProteinEntry, ...] = Field(
        default_factory=tuple
    )
    explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unexplained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_ambiguities: tuple[ProteinParsimonyAmbiguityEntry, ...] = Field(
        default_factory=tuple
    )
    variant_comparison: ParsimonyVariantComparisonReport
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


def build_protein_parsimony_report(
    records: tuple[PsmRecord, ...],
    *,
    variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
    review_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> ProteinParsimonyReport:
    """Build one named protein parsimony result with unresolved ambiguity ledgers."""
    normalized_review_variants = tuple(dict.fromkeys(review_variants))
    if not normalized_review_variants:
        raise ValueError("review_variants must not be empty")
    if variant not in normalized_review_variants:
        normalized_review_variants = (variant, *normalized_review_variants)

    peptide_rollups = tuple(
        peptide
        for peptide in rollup_peptide_evidence(records)
        if peptide.target_decoy_label is not TargetDecoyLabel.DECOY
    )
    total_peptides = tuple(peptide.canonical_peptide for peptide in peptide_rollups)
    variant_results = {
        review_variant: _infer_selected_groups(records, variant=review_variant)
        for review_variant in normalized_review_variants
    }
    selected_groups = variant_results[variant]

    shared_selected_proteins_by_peptide: dict[str, tuple[str, ...]] = {}
    for peptide in total_peptides:
        candidate_proteins = tuple(
            sorted(
                entry.protein_ref
                for entry in selected_groups
                if peptide in entry.covered_peptides
            )
        )
        if len(candidate_proteins) > 1:
            shared_selected_proteins_by_peptide[peptide] = candidate_proteins

    selected_entries = tuple(
        ProteinParsimonyProteinEntry(
            variant=entry.variant,
            selection_rank=entry.selection_rank,
            protein_ref=entry.protein_ref,
            source_group_id=entry.source_group_id,
            group_protein_refs=entry.group_protein_refs,
            covered_peptides=entry.covered_peptides,
            newly_explained_peptides=entry.newly_explained_peptides,
            unresolved_shared_peptides=tuple(
                peptide
                for peptide in entry.covered_peptides
                if peptide in shared_selected_proteins_by_peptide
            ),
            best_score=entry.best_score,
            best_q_value=entry.best_q_value,
            target_decoy_label=entry.target_decoy_label,
        )
        for entry in selected_groups
    )

    explained_peptides = tuple(
        sorted(
            {
                peptide
                for entry in selected_entries
                for peptide in entry.newly_explained_peptides
            }
        )
    )
    unexplained_peptides = tuple(
        peptide for peptide in total_peptides if peptide not in explained_peptides
    )

    ambiguities: list[ProteinParsimonyAmbiguityEntry] = []
    for peptide, candidate_proteins in sorted(
        shared_selected_proteins_by_peptide.items()
    ):
        ambiguities.append(
            ProteinParsimonyAmbiguityEntry(
                subject_id=peptide,
                kind=InferenceDisagreementKind.PEPTIDE_ASSIGNMENT,
                candidate_proteins=candidate_proteins,
                strategy_assignments={
                    review_variant.value: tuple(
                        sorted(
                            entry.protein_ref
                            for entry in variant_results[review_variant]
                            if peptide in entry.covered_peptides
                        )
                    )
                    for review_variant in normalized_review_variants
                },
                note="shared peptide remains explained by multiple selected proteins under the reviewed parsimony policies",
            )
        )

    variant_comparison = _compare_selected_groups(
        tuple(variant_results[review_variant] for review_variant in normalized_review_variants)
    )
    for difference in variant_comparison.differences:
        if (
            not difference.left_only_proteins
            and not difference.right_only_proteins
            and difference.first_difference_rank is None
        ):
            continue
        ambiguities.append(
            ProteinParsimonyAmbiguityEntry(
                subject_id=(
                    f"{difference.left_variant.value}__vs__"
                    f"{difference.right_variant.value}"
                ),
                kind=InferenceDisagreementKind.PROTEIN_SET,
                candidate_proteins=tuple(
                    sorted(
                        set(difference.shared_selected_proteins)
                        | set(difference.left_only_proteins)
                        | set(difference.right_only_proteins)
                    )
                ),
                strategy_assignments={
                    difference.left_variant.value: tuple(
                        entry.protein_ref
                        for entry in variant_results[difference.left_variant]
                    ),
                    difference.right_variant.value: tuple(
                        entry.protein_ref
                        for entry in variant_results[difference.right_variant]
                    ),
                },
                first_difference_rank=difference.first_difference_rank,
                note="named parsimony variants diverge in protein-set membership or ranking over the same peptide evidence",
            )
        )

    summary = ProteinParsimonySummary(
        variant=variant,
        review_variants=normalized_review_variants,
        total_observed_peptides=len(total_peptides),
        explained_peptide_count=len(explained_peptides),
        unexplained_peptide_count=len(unexplained_peptides),
        selected_protein_count=len(selected_entries),
        shared_selected_peptide_count=len(shared_selected_proteins_by_peptide),
        variant_difference_count=sum(
            1
            for entry in ambiguities
            if entry.kind is InferenceDisagreementKind.PROTEIN_SET
        ),
        unresolved_ambiguity_count=len(ambiguities),
    )
    report = ProteinParsimonyReport(
        summary=summary,
        selected_proteins=selected_entries,
        explained_peptides=explained_peptides,
        unexplained_peptides=unexplained_peptides,
        unresolved_ambiguities=tuple(ambiguities),
        variant_comparison=variant_comparison,
        reproducibility_hash="0" * 64,
    )
    return report.model_copy(
        update={"reproducibility_hash": hashlib.sha256(_raw_payload(report)).hexdigest()}
    )


def render_protein_parsimony_summary_tsv(report: ProteinParsimonyReport) -> str:
    """Render the protein parsimony summary ledger as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("metric", "value"))
    for metric, value in (
        ("variant", report.summary.variant.value),
        (
            "review_variants",
            ";".join(variant.value for variant in report.summary.review_variants),
        ),
        ("total_observed_peptides", report.summary.total_observed_peptides),
        ("explained_peptide_count", report.summary.explained_peptide_count),
        ("unexplained_peptide_count", report.summary.unexplained_peptide_count),
        ("selected_protein_count", report.summary.selected_protein_count),
        ("shared_selected_peptide_count", report.summary.shared_selected_peptide_count),
        ("variant_difference_count", report.summary.variant_difference_count),
        ("unresolved_ambiguity_count", report.summary.unresolved_ambiguity_count),
        ("reproducibility_hash", report.reproducibility_hash),
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_protein_parsimony_proteins_tsv(report: ProteinParsimonyReport) -> str:
    """Render the selected protein parsimony set as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "variant",
            "selection_rank",
            "protein_ref",
            "source_group_id",
            "group_protein_refs",
            "covered_peptides",
            "newly_explained_peptides",
            "unresolved_shared_peptides",
            "best_score",
            "best_q_value",
            "target_decoy_label",
        )
    )
    for entry in report.selected_proteins:
        writer.writerow(
            (
                entry.variant.value,
                entry.selection_rank,
                entry.protein_ref,
                entry.source_group_id,
                ";".join(entry.group_protein_refs),
                ";".join(entry.covered_peptides),
                ";".join(entry.newly_explained_peptides),
                ";".join(entry.unresolved_shared_peptides),
                entry.best_score,
                "" if entry.best_q_value is None else entry.best_q_value,
                entry.target_decoy_label.value,
            )
        )
    return buffer.getvalue()


def render_protein_parsimony_ambiguities_tsv(report: ProteinParsimonyReport) -> str:
    """Render unresolved protein parsimony ambiguities as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "subject_id",
            "kind",
            "candidate_proteins",
            "first_difference_rank",
            "strategy_assignments",
            "note",
        )
    )
    for entry in report.unresolved_ambiguities:
        writer.writerow(
            (
                entry.subject_id,
                entry.kind.value,
                ";".join(entry.candidate_proteins),
                "" if entry.first_difference_rank is None else entry.first_difference_rank,
                _render_strategy_assignments(entry.strategy_assignments),
                entry.note,
            )
        )
    return buffer.getvalue()


def _infer_selected_groups(
    records: tuple[PsmRecord, ...],
    *,
    variant: ParsimonyVariant,
) -> tuple[ProteinParsimonyProteinEntry, ...]:
    grouping_report = build_protein_grouping_report(records)
    remaining = {
        peptide.canonical_peptide
        for peptide in rollup_peptide_evidence(records)
        if peptide.target_decoy_label is not TargetDecoyLabel.DECOY
    }
    selected: list[ProteinParsimonyProteinEntry] = []
    available = list(grouping_report.groups)
    rank = 1
    while remaining:
        scored_candidates: list[tuple[ProteinGroupingEntry, tuple[str, ...]]] = []
        for group in available:
            newly_explained = tuple(sorted(set(group.peptides) & remaining))
            if not newly_explained:
                continue
            scored_candidates.append((group, newly_explained))
        if not scored_candidates:
            break
        scored_candidates.sort(
            key=lambda item: _parsimony_sort_key(item[0], item[1], variant)
        )
        group, newly_explained = scored_candidates[0]
        selected.append(
            ProteinParsimonyProteinEntry(
                variant=variant,
                selection_rank=rank,
                protein_ref=group.representative_protein,
                source_group_id=group.group_id,
                group_protein_refs=group.protein_refs,
                covered_peptides=group.peptides,
                newly_explained_peptides=newly_explained,
                unresolved_shared_peptides=tuple(),
                best_score=group.best_score,
                best_q_value=group.best_q_value,
                target_decoy_label=group.target_decoy_label,
            )
        )
        remaining -= set(newly_explained)
        available = [entry for entry in available if entry.group_id != group.group_id]
        rank += 1
    return tuple(selected)


def _compare_selected_groups(
    results: tuple[tuple[ProteinParsimonyProteinEntry, ...], ...],
) -> ParsimonyVariantComparisonReport:
    comparison_results = tuple(
        ParsimonyVariantResult(
            variant=entries[0].variant if entries else ParsimonyVariant.GREEDY_COVERAGE,
            selected_proteins=tuple(
                ParsimonyProteinEntry(
                    variant=entry.variant,
                    selection_rank=entry.selection_rank,
                    protein_ref=entry.protein_ref,
                    source_group_id=entry.source_group_id,
                    covered_peptides=entry.covered_peptides,
                    newly_explained_peptides=entry.newly_explained_peptides,
                    best_score=entry.best_score,
                    best_q_value=entry.best_q_value,
                    target_decoy_label=entry.target_decoy_label,
                )
                for entry in entries
            ),
        )
        for entries in results
    )
    differences: list[ParsimonyVariantDifferenceEntry] = []
    for left_index, left in enumerate(comparison_results):
        for right in comparison_results[left_index + 1 :]:
            left_order = [entry.protein_ref for entry in left.selected_proteins]
            right_order = [entry.protein_ref for entry in right.selected_proteins]
            first_difference_rank = next(
                (
                    rank
                    for rank, (left_ref, right_ref) in enumerate(
                        zip(left_order, right_order, strict=False),
                        start=1,
                    )
                    if left_ref != right_ref
                ),
                None,
            )
            if first_difference_rank is None and len(left_order) != len(right_order):
                first_difference_rank = min(len(left_order), len(right_order)) + 1
            left_set = set(left_order)
            right_set = set(right_order)
            differences.append(
                ParsimonyVariantDifferenceEntry(
                    left_variant=left.variant,
                    right_variant=right.variant,
                    first_difference_rank=first_difference_rank,
                    shared_selected_proteins=tuple(sorted(left_set & right_set)),
                    left_only_proteins=tuple(sorted(left_set - right_set)),
                    right_only_proteins=tuple(sorted(right_set - left_set)),
                )
            )
    return ParsimonyVariantComparisonReport(
        results=comparison_results,
        differences=tuple(differences),
    )


def _parsimony_sort_key(
    group: ProteinGroupingEntry,
    newly_explained: tuple[str, ...],
    variant: ParsimonyVariant,
) -> tuple[float | int | str, ...]:
    if variant is ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY:
        return (
            -group.unique_peptide_count,
            -len(newly_explained),
            -group.best_score,
            group.representative_protein,
        )
    if variant is ParsimonyVariant.BEST_SCORE_PRIORITY:
        return (
            -group.best_score,
            -len(newly_explained),
            -group.unique_peptide_count,
            group.representative_protein,
        )
    return (
        -len(newly_explained),
        -group.unique_peptide_count,
        -group.best_score,
        group.representative_protein,
    )


def _render_strategy_assignments(
    assignments: dict[str, tuple[str, ...]],
) -> str:
    return "|".join(
        f"{strategy}:{';'.join(proteins)}"
        for strategy, proteins in sorted(assignments.items())
    )


def _raw_payload(report: ProteinParsimonyReport) -> bytes:
    payload = {
        "summary": {
            "variant": report.summary.variant.value,
            "review_variants": [variant.value for variant in report.summary.review_variants],
            "total_observed_peptides": report.summary.total_observed_peptides,
            "explained_peptide_count": report.summary.explained_peptide_count,
            "unexplained_peptide_count": report.summary.unexplained_peptide_count,
            "selected_protein_count": report.summary.selected_protein_count,
            "shared_selected_peptide_count": report.summary.shared_selected_peptide_count,
            "variant_difference_count": report.summary.variant_difference_count,
            "unresolved_ambiguity_count": report.summary.unresolved_ambiguity_count,
        },
        "selected_proteins": [entry.to_dict() for entry in report.selected_proteins],
        "explained_peptides": list(report.explained_peptides),
        "unexplained_peptides": list(report.unexplained_peptides),
        "unresolved_ambiguities": [entry.to_dict() for entry in report.unresolved_ambiguities],
        "variant_comparison": report.variant_comparison.to_dict(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
