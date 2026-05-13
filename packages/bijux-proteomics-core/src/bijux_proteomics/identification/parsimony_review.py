# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Reviewer-facing protein parsimony reporting."""

from __future__ import annotations

import csv
import io

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    InferenceDisagreementKind,
    ParsimonyProteinEntry,
    ParsimonyVariant,
    ProteinGroupEntry,
    TargetDecoyLabel,
    build_protein_groups,
    compare_parsimony_variants,
    infer_proteins_by_parsimony,
    rollup_peptide_evidence,
)
from bijux_proteomics_foundation import JsonModel


class ParsimonyReviewSummary(JsonModel):
    """Compact summary over one named parsimony review."""

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


class ParsimonyReviewProteinEntry(JsonModel):
    """One selected protein inside the named parsimony review."""

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


class ParsimonyAmbiguityEntry(JsonModel):
    """One unresolved ambiguity left after parsimony review."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(..., min_length=1)
    kind: InferenceDisagreementKind
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    strategy_assignments: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    first_difference_rank: int | None = Field(default=None, ge=1)
    note: str = Field(..., min_length=1)


class ParsimonyReviewReport(JsonModel):
    """One review packet over parsimony-selected proteins and remaining ambiguity."""

    model_config = ConfigDict(extra="forbid")

    summary: ParsimonyReviewSummary
    selected_proteins: tuple[ParsimonyReviewProteinEntry, ...] = Field(
        default_factory=tuple
    )
    unexplained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_ambiguities: tuple[ParsimonyAmbiguityEntry, ...] = Field(
        default_factory=tuple
    )


def build_parsimony_review_report(
    records: tuple,
    *,
    variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
    review_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> ParsimonyReviewReport:
    """Build a direct review packet over one named parsimony result."""
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
    selected = infer_proteins_by_parsimony(records, variant=variant)
    group_lookup = {
        group.group_id: group for group in build_protein_groups(records)
    }
    variant_results = {
        review_variant: infer_proteins_by_parsimony(records, variant=review_variant)
        for review_variant in normalized_review_variants
    }

    shared_selected_proteins_by_peptide: dict[str, tuple[str, ...]] = {}
    for peptide in total_peptides:
        candidate_proteins = tuple(
            sorted(
                entry.protein_ref
                for entry in selected
                if peptide in entry.covered_peptides
            )
        )
        if len(candidate_proteins) > 1:
            shared_selected_proteins_by_peptide[peptide] = candidate_proteins

    selected_entries = tuple(
        _build_selected_entry(
            entry=entry,
            group=group_lookup[entry.source_group_id],
            unresolved_shared_peptides=tuple(
                peptide
                for peptide in entry.covered_peptides
                if peptide in shared_selected_proteins_by_peptide
            ),
        )
        for entry in selected
    )

    explained_peptides = tuple(
        sorted(
            {
                peptide
                for entry in selected
                for peptide in entry.newly_explained_peptides
            }
        )
    )
    unexplained_peptides = tuple(
        peptide for peptide in total_peptides if peptide not in explained_peptides
    )

    ambiguities: list[ParsimonyAmbiguityEntry] = []
    for peptide, candidate_proteins in sorted(shared_selected_proteins_by_peptide.items()):
        ambiguities.append(
            ParsimonyAmbiguityEntry(
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

    comparison = compare_parsimony_variants(records, variants=normalized_review_variants)
    for difference in comparison.differences:
        if (
            not difference.left_only_proteins
            and not difference.right_only_proteins
            and difference.first_difference_rank is None
        ):
            continue
        ambiguities.append(
            ParsimonyAmbiguityEntry(
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

    return ParsimonyReviewReport(
        summary=ParsimonyReviewSummary(
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
        ),
        selected_proteins=selected_entries,
        unexplained_peptides=unexplained_peptides,
        unresolved_ambiguities=tuple(ambiguities),
    )


def render_parsimony_review_summary_tsv(report: ParsimonyReviewReport) -> str:
    """Render the parsimony summary ledger as TSV."""
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
    ):
        writer.writerow((metric, value))
    return buffer.getvalue()


def render_parsimony_review_proteins_tsv(report: ParsimonyReviewReport) -> str:
    """Render the selected parsimony proteins as TSV."""
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


def render_parsimony_review_ambiguities_tsv(report: ParsimonyReviewReport) -> str:
    """Render unresolved parsimony ambiguities as TSV."""
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


def _build_selected_entry(
    *,
    entry: ParsimonyProteinEntry,
    group: ProteinGroupEntry,
    unresolved_shared_peptides: tuple[str, ...],
) -> ParsimonyReviewProteinEntry:
    return ParsimonyReviewProteinEntry(
        variant=entry.variant,
        selection_rank=entry.selection_rank,
        protein_ref=entry.protein_ref,
        source_group_id=entry.source_group_id,
        group_protein_refs=group.protein_refs,
        covered_peptides=entry.covered_peptides,
        newly_explained_peptides=entry.newly_explained_peptides,
        unresolved_shared_peptides=unresolved_shared_peptides,
        best_score=entry.best_score,
        best_q_value=entry.best_q_value,
        target_decoy_label=entry.target_decoy_label,
    )


def _render_strategy_assignments(
    assignments: dict[str, tuple[str, ...]],
) -> str:
    return "|".join(
        f"{strategy}:{';'.join(proteins)}"
        for strategy, proteins in sorted(assignments.items())
    )
