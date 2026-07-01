# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Detect and reduce redundant biomarker candidates before targeted panel assembly."""

from __future__ import annotations

from collections.abc import Mapping
import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
import math
from statistics import mean

from pydantic import ConfigDict, Field

from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_qc import (
    TargetedTargetQcEntry,
    build_targeted_assay_qc_report,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics_foundation import JsonModel


class PanelRedundancyReasonCode(StrEnum):
    """Stable reasons behind one redundancy cluster or dropped candidate."""

    SAME_TARGET_PROTEIN = "same_target_protein"
    HIGH_SIGNAL_CORRELATION = "high_signal_correlation"
    SHARED_PEPTIDE_ASSAY = "shared_peptide_assay"
    LOWER_SCORING_CLUSTER_MEMBER = "lower_scoring_cluster_member"
    LOWER_PRIORITY_CLUSTER_MEMBER = "lower_priority_cluster_member"


class PanelRedundancyCandidateInput(JsonModel):
    """Biomarker candidate input shape accepted by panel redundancy analysis."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class PanelRedundancyPolicy(JsonModel):
    """Policy controlling biomarker redundancy clustering and representative selection."""

    model_config = ConfigDict(extra="forbid")

    minimum_shared_samples: int = Field(default=4, ge=2)
    correlation_threshold: float = Field(default=0.95, ge=0.0, le=1.0)


class PanelRedundancyPairEntry(JsonModel):
    """One pairwise redundancy relation between two biomarker candidates."""

    model_config = ConfigDict(extra="forbid")

    left_candidate_id: str = Field(..., min_length=1)
    right_candidate_id: str = Field(..., min_length=1)
    shared_sample_count: int = Field(..., ge=0)
    correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    reason_codes: tuple[PanelRedundancyReasonCode, ...] = Field(default_factory=tuple)
    redundant: bool
    note: str = Field(..., min_length=1)


class PanelRedundancyClusterEntry(JsonModel):
    """One redundancy cluster with an explicit retained representative."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(..., min_length=1)
    representative_candidate_id: str = Field(..., min_length=1)
    member_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    dropped_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    shared_reason_codes: tuple[PanelRedundancyReasonCode, ...] = Field(
        default_factory=tuple
    )
    member_count: int = Field(..., ge=1)
    dropped_count: int = Field(..., ge=0)
    median_redundant_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    note: str = Field(..., min_length=1)


class PanelRedundancyCandidateEntry(JsonModel):
    """One candidate-level redundancy decision for panel reduction."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    original_priority_rank: int = Field(..., ge=1)
    reduced_priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    cluster_id: str = Field(..., min_length=1)
    representative_candidate_id: str = Field(..., min_length=1)
    representative: bool
    dropped: bool
    shared_sample_count: int = Field(..., ge=0)
    max_redundant_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)
    redundancy_reason_codes: tuple[PanelRedundancyReasonCode, ...] = Field(
        default_factory=tuple
    )
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PanelRedundancySummary(JsonModel):
    """Compact summary over one panel redundancy analysis pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    redundancy_pair_count: int = Field(..., ge=0)
    cluster_count: int = Field(..., ge=0)
    representative_candidate_count: int = Field(..., ge=0)
    dropped_candidate_count: int = Field(..., ge=0)


class PanelRedundancyReport(JsonModel):
    """Owned biomarker redundancy analysis for targeted panel size reduction."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    policy: PanelRedundancyPolicy
    pairs: tuple[PanelRedundancyPairEntry, ...] = Field(default_factory=tuple)
    clusters: tuple[PanelRedundancyClusterEntry, ...] = Field(default_factory=tuple)
    candidates: tuple[PanelRedundancyCandidateEntry, ...] = Field(default_factory=tuple)
    summary: PanelRedundancySummary
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _ImportedTargetDescriptor:
    target_id: str
    peptide_sequence: str
    precursor_charge: int | None
    protein_refs: tuple[str, ...]


def build_panel_redundancy_report(
    biomarker_candidates: tuple[PanelRedundancyCandidateInput, ...],
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...],
    import_report: TargetedResultImportReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: PanelRedundancyPolicy | None = None,
) -> PanelRedundancyReport:
    """Reduce highly redundant biomarker candidates into representative panel markers."""

    active_policy = policy or PanelRedundancyPolicy()
    assay_qc_report = build_targeted_assay_qc_report(import_report, design_entries)
    descriptors = _build_imported_target_descriptors(import_report)
    qc_by_target_sample = {
        (entry.target_id, entry.sample_id): entry for entry in assay_qc_report.target_qc
    }
    design_by_sample = {
        entry.sample_id: entry
        for entry in design_entries
        if entry.sample_id in {item.sample_id for item in import_report.observations}
    }
    assays_by_candidate: dict[str, list[TargetedValidationPanelAssayInput]] = {}
    for assay in panel_assays:
        assays_by_candidate.setdefault(assay.biomarker_candidate_id, []).append(assay)

    candidate_vectors: dict[str, dict[str, float]] = {}
    candidate_assay_keys: dict[str, set[tuple[str, int]]] = {}
    for candidate in biomarker_candidates:
        assays = tuple(
            sorted(
                assays_by_candidate.get(candidate.candidate_id, ()),
                key=lambda item: item.assay_entry_id,
            )
        )
        candidate_vectors[candidate.candidate_id] = _build_candidate_vector(
            candidate=candidate,
            assays=assays,
            descriptors=descriptors,
            qc_by_target_sample=qc_by_target_sample,
            design_by_sample=design_by_sample,
        )
        candidate_assay_keys[candidate.candidate_id] = {
            (assay.canonical_peptide, assay.precursor_charge) for assay in assays
        }

    pairs: list[PanelRedundancyPairEntry] = []
    redundant_neighbors: dict[str, set[str]] = {
        candidate.candidate_id: set() for candidate in biomarker_candidates
    }
    pair_lookup: dict[tuple[str, str], PanelRedundancyPairEntry] = {}
    sorted_candidates = sorted(biomarker_candidates, key=lambda item: item.candidate_id)
    for index, left in enumerate(sorted_candidates):
        for right in sorted_candidates[index + 1 :]:
            pair_entry = _build_pair_entry(
                left=left,
                right=right,
                left_vector=candidate_vectors[left.candidate_id],
                right_vector=candidate_vectors[right.candidate_id],
                left_assay_keys=candidate_assay_keys[left.candidate_id],
                right_assay_keys=candidate_assay_keys[right.candidate_id],
                policy=active_policy,
            )
            pairs.append(pair_entry)
            pair_lookup[(left.candidate_id, right.candidate_id)] = pair_entry
            pair_lookup[(right.candidate_id, left.candidate_id)] = pair_entry
            if pair_entry.redundant:
                redundant_neighbors[left.candidate_id].add(right.candidate_id)
                redundant_neighbors[right.candidate_id].add(left.candidate_id)

    clusters = _build_clusters(
        biomarker_candidates=tuple(
            sorted(
                biomarker_candidates,
                key=lambda item: (
                    item.priority_rank,
                    -item.final_score,
                    item.candidate_id,
                ),
            )
        ),
        redundant_neighbors=redundant_neighbors,
        pair_lookup=pair_lookup,
    )
    candidate_entries = _build_candidate_entries(
        biomarker_candidates=biomarker_candidates,
        clusters=clusters,
        redundant_neighbors=redundant_neighbors,
        pair_lookup=pair_lookup,
    )

    return PanelRedundancyReport(
        source_name=import_report.source_name,
        policy=active_policy,
        pairs=tuple(
            sorted(
                pairs,
                key=lambda item: (item.left_candidate_id, item.right_candidate_id),
            )
        ),
        clusters=clusters,
        candidates=candidate_entries,
        summary=PanelRedundancySummary(
            candidate_count=len(candidate_entries),
            redundancy_pair_count=sum(item.redundant for item in pairs),
            cluster_count=len(clusters),
            representative_candidate_count=sum(
                item.representative for item in candidate_entries
            ),
            dropped_candidate_count=sum(item.dropped for item in candidate_entries),
        ),
        note=(
            "panel redundancy analysis clusters highly correlated or biologically duplicate "
            "biomarkers across the full targeted validation sample set so panel size can be "
            "reduced with explicit representative and dropped-candidate reasoning"
        ),
    )


def render_panel_redundancy_summary_tsv(report: PanelRedundancyReport) -> str:
    """Render panel redundancy summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("candidate_count", report.summary.candidate_count))
    writer.writerow(("redundancy_pair_count", report.summary.redundancy_pair_count))
    writer.writerow(("cluster_count", report.summary.cluster_count))
    writer.writerow(
        (
            "representative_candidate_count",
            report.summary.representative_candidate_count,
        )
    )
    writer.writerow(("dropped_candidate_count", report.summary.dropped_candidate_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_panel_redundancy_cluster_tsv(report: PanelRedundancyReport) -> str:
    """Render redundancy clusters and representatives as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "cluster_id",
            "representative_candidate_id",
            "member_candidate_ids",
            "dropped_candidate_ids",
            "shared_reason_codes",
            "member_count",
            "dropped_count",
            "median_redundant_correlation",
            "note",
        )
    )
    for entry in report.clusters:
        writer.writerow(
            (
                entry.cluster_id,
                entry.representative_candidate_id,
                ";".join(entry.member_candidate_ids),
                ";".join(entry.dropped_candidate_ids),
                ";".join(reason.value for reason in entry.shared_reason_codes),
                entry.member_count,
                entry.dropped_count,
                _format_float(entry.median_redundant_correlation),
                entry.note,
            )
        )
    return handle.getvalue()


def render_panel_redundancy_candidate_tsv(report: PanelRedundancyReport) -> str:
    """Render candidate-level redundancy decisions in panel-builder-compatible TSV form."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "penalty_total",
            "rank_reason_codes",
            "ranking_note",
            "cluster_id",
            "representative_candidate_id",
            "representative",
            "dropped",
            "shared_sample_count",
            "max_redundant_correlation",
            "redundancy_reason_codes",
        )
    )
    for entry in report.candidates:
        writer.writerow(
            (
                entry.candidate_id,
                entry.candidate_kind.value,
                entry.display_label,
                entry.target_protein_ref,
                "" if entry.site_key is None else entry.site_key,
                entry.reduced_priority_rank,
                _format_float(entry.final_score),
                _format_float(entry.penalty_total),
                ";".join(entry.rank_reason_codes),
                entry.note,
                entry.cluster_id,
                entry.representative_candidate_id,
                str(entry.representative).lower(),
                str(entry.dropped).lower(),
                entry.shared_sample_count,
                _format_float(entry.max_redundant_correlation),
                ";".join(reason.value for reason in entry.redundancy_reason_codes),
            )
        )
    return handle.getvalue()


def render_panel_redundancy_dropped_tsv(report: PanelRedundancyReport) -> str:
    """Render only dropped redundant candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "candidate_id",
            "cluster_id",
            "representative_candidate_id",
            "shared_sample_count",
            "max_redundant_correlation",
            "redundancy_reason_codes",
            "note",
        )
    )
    for entry in report.candidates:
        if not entry.dropped:
            continue
        writer.writerow(
            (
                entry.candidate_id,
                entry.cluster_id,
                entry.representative_candidate_id,
                entry.shared_sample_count,
                _format_float(entry.max_redundant_correlation),
                ";".join(reason.value for reason in entry.redundancy_reason_codes),
                entry.note,
            )
        )
    return handle.getvalue()


def _build_clusters(
    *,
    biomarker_candidates: tuple[PanelRedundancyCandidateInput, ...],
    redundant_neighbors: dict[str, set[str]],
    pair_lookup: dict[tuple[str, str], PanelRedundancyPairEntry],
) -> tuple[PanelRedundancyClusterEntry, ...]:
    candidate_by_id = {
        candidate.candidate_id: candidate for candidate in biomarker_candidates
    }
    visited: set[str] = set()
    clusters: list[PanelRedundancyClusterEntry] = []
    cluster_index = 0
    for candidate in biomarker_candidates:
        if candidate.candidate_id in visited:
            continue
        component = _connected_component(
            candidate.candidate_id, redundant_neighbors, visited
        )
        cluster_index += 1
        ordered_members = tuple(
            sorted(
                component,
                key=lambda candidate_id: (
                    candidate_by_id[candidate_id].priority_rank,
                    -candidate_by_id[candidate_id].final_score,
                    candidate_id,
                ),
            )
        )
        representative = ordered_members[0]
        dropped = ordered_members[1:]
        pair_entries = [
            pair_lookup[(left, right)]
            for index, left in enumerate(ordered_members)
            for right in ordered_members[index + 1 :]
            if pair_lookup[(left, right)].redundant
        ]
        shared_reasons = tuple(
            dict.fromkeys(
                reason for pair in pair_entries for reason in pair.reason_codes
            )
        )
        redundant_correlations = [
            pair.correlation for pair in pair_entries if pair.correlation is not None
        ]
        clusters.append(
            PanelRedundancyClusterEntry(
                cluster_id=f"cluster:{cluster_index:03d}",
                representative_candidate_id=representative,
                member_candidate_ids=ordered_members,
                dropped_candidate_ids=dropped,
                shared_reason_codes=shared_reasons,
                member_count=len(ordered_members),
                dropped_count=len(dropped),
                median_redundant_correlation=(
                    None
                    if not redundant_correlations
                    else mean(sorted(redundant_correlations))
                ),
                note=(
                    f"{representative} retains the highest-ranked representative position within "
                    f"a redundancy cluster of {len(ordered_members)} candidates"
                ),
            )
        )
    return tuple(sorted(clusters, key=lambda item: item.cluster_id))


def _build_candidate_entries(
    *,
    biomarker_candidates: tuple[PanelRedundancyCandidateInput, ...],
    clusters: tuple[PanelRedundancyClusterEntry, ...],
    redundant_neighbors: dict[str, set[str]],
    pair_lookup: dict[tuple[str, str], PanelRedundancyPairEntry],
) -> tuple[PanelRedundancyCandidateEntry, ...]:
    cluster_by_candidate = {
        candidate_id: cluster
        for cluster in clusters
        for candidate_id in cluster.member_candidate_ids
    }
    candidate_by_id = {
        candidate.candidate_id: candidate for candidate in biomarker_candidates
    }
    entries: list[PanelRedundancyCandidateEntry] = []
    representatives = [
        candidate_id
        for cluster in clusters
        for candidate_id in cluster.member_candidate_ids
        if candidate_id == cluster.representative_candidate_id
    ]
    representative_rank = {
        candidate_id: index
        for index, candidate_id in enumerate(representatives, start=1)
    }
    dropped_rank_start = len(representatives) + 1
    dropped_rank = dropped_rank_start
    for candidate in sorted(
        biomarker_candidates,
        key=lambda item: (
            item.priority_rank,
            -item.final_score,
            item.candidate_id,
        ),
    ):
        cluster = cluster_by_candidate[candidate.candidate_id]
        representative = candidate.candidate_id == cluster.representative_candidate_id
        dropped = candidate.candidate_id in cluster.dropped_candidate_ids
        pair_entries = [
            pair_lookup[(candidate.candidate_id, neighbor)]
            for neighbor in sorted(redundant_neighbors[candidate.candidate_id])
            if pair_lookup[(candidate.candidate_id, neighbor)].redundant
        ]
        max_corr = max(
            (
                entry.correlation
                for entry in pair_entries
                if entry.correlation is not None
            ),
            default=None,
        )
        shared_samples = max(
            (entry.shared_sample_count for entry in pair_entries), default=0
        )
        reason_codes = list(cluster.shared_reason_codes)
        if dropped:
            if (
                candidate.final_score
                < candidate_by_id[cluster.representative_candidate_id].final_score
            ):
                reason_codes.append(
                    PanelRedundancyReasonCode.LOWER_SCORING_CLUSTER_MEMBER
                )
            if (
                candidate.priority_rank
                > candidate_by_id[cluster.representative_candidate_id].priority_rank
            ):
                reason_codes.append(
                    PanelRedundancyReasonCode.LOWER_PRIORITY_CLUSTER_MEMBER
                )
        deduped_reasons = tuple(dict.fromkeys(reason_codes))
        if representative:
            reduced_rank = representative_rank[candidate.candidate_id]
        else:
            reduced_rank = dropped_rank
            dropped_rank += 1
        entries.append(
            PanelRedundancyCandidateEntry(
                candidate_id=candidate.candidate_id,
                candidate_kind=candidate.candidate_kind,
                display_label=candidate.display_label,
                target_protein_ref=candidate.target_protein_ref,
                site_key=candidate.site_key,
                original_priority_rank=candidate.priority_rank,
                reduced_priority_rank=reduced_rank,
                final_score=candidate.final_score,
                penalty_total=candidate.penalty_total,
                cluster_id=cluster.cluster_id,
                representative_candidate_id=cluster.representative_candidate_id,
                representative=representative,
                dropped=dropped,
                shared_sample_count=shared_samples,
                max_redundant_correlation=max_corr,
                redundancy_reason_codes=deduped_reasons,
                rank_reason_codes=candidate.rank_reason_codes,
                note=(
                    f"{candidate.candidate_id} is retained as the representative for {cluster.cluster_id}"
                    if representative
                    else f"{candidate.candidate_id} is dropped from {cluster.cluster_id} in favor of {cluster.representative_candidate_id}"
                ),
            )
        )
    return tuple(
        sorted(
            entries,
            key=lambda item: (
                item.reduced_priority_rank,
                item.original_priority_rank,
                item.candidate_id,
            ),
        )
    )


def _connected_component(
    root_candidate_id: str,
    redundant_neighbors: dict[str, set[str]],
    visited: set[str],
) -> set[str]:
    stack = [root_candidate_id]
    component: set[str] = set()
    while stack:
        candidate_id = stack.pop()
        if candidate_id in visited:
            continue
        visited.add(candidate_id)
        component.add(candidate_id)
        stack.extend(sorted(redundant_neighbors[candidate_id] - visited))
    return component


def _build_pair_entry(
    *,
    left: PanelRedundancyCandidateInput,
    right: PanelRedundancyCandidateInput,
    left_vector: dict[str, float],
    right_vector: dict[str, float],
    left_assay_keys: set[tuple[str, int]],
    right_assay_keys: set[tuple[str, int]],
    policy: PanelRedundancyPolicy,
) -> PanelRedundancyPairEntry:
    reasons: list[PanelRedundancyReasonCode] = []
    if left.target_protein_ref == right.target_protein_ref:
        reasons.append(PanelRedundancyReasonCode.SAME_TARGET_PROTEIN)
    if left_assay_keys.intersection(right_assay_keys):
        reasons.append(PanelRedundancyReasonCode.SHARED_PEPTIDE_ASSAY)
    shared_samples = sorted(set(left_vector).intersection(right_vector))
    correlation = None
    if len(shared_samples) >= policy.minimum_shared_samples:
        correlation = _pearson_correlation(
            [left_vector[sample_id] for sample_id in shared_samples],
            [right_vector[sample_id] for sample_id in shared_samples],
        )
        if correlation is not None and correlation >= policy.correlation_threshold:
            reasons.append(PanelRedundancyReasonCode.HIGH_SIGNAL_CORRELATION)
    redundant = bool(reasons) and (
        PanelRedundancyReasonCode.SAME_TARGET_PROTEIN in reasons
        or PanelRedundancyReasonCode.SHARED_PEPTIDE_ASSAY in reasons
        or PanelRedundancyReasonCode.HIGH_SIGNAL_CORRELATION in reasons
    )
    return PanelRedundancyPairEntry(
        left_candidate_id=left.candidate_id,
        right_candidate_id=right.candidate_id,
        shared_sample_count=len(shared_samples),
        correlation=correlation,
        reason_codes=tuple(dict.fromkeys(reasons)),
        redundant=redundant,
        note=(
            f"{left.candidate_id} and {right.candidate_id} share redundant biomarker behavior"
            if redundant
            else f"{left.candidate_id} and {right.candidate_id} remain distinct after panel redundancy analysis"
        ),
    )


def _build_candidate_vector(
    *,
    candidate: PanelRedundancyCandidateInput,
    assays: tuple[TargetedValidationPanelAssayInput, ...],
    descriptors: tuple[_ImportedTargetDescriptor, ...],
    qc_by_target_sample: Mapping[tuple[str, str], TargetedTargetQcEntry],
    design_by_sample: dict[str, ExperimentalDesignEntry],
) -> dict[str, float]:
    target_ids: set[str] = set()
    for assay in assays:
        target_ids.update(_match_assay_target_ids(assay, descriptors))
    sample_values: dict[str, list[float]] = {}
    for sample_id in design_by_sample:
        for target_id in target_ids:
            qc_entry = qc_by_target_sample.get((target_id, sample_id))
            if (
                qc_entry is None
                or not qc_entry.reliable
                or qc_entry.passing_total_intensity is None
                or qc_entry.passing_total_intensity <= 0.0
            ):
                continue
            sample_values.setdefault(sample_id, []).append(
                math.log2(qc_entry.passing_total_intensity)
            )
    return {
        sample_id: mean(values) for sample_id, values in sample_values.items() if values
    }


def _build_imported_target_descriptors(
    import_report: TargetedResultImportReport,
) -> tuple[_ImportedTargetDescriptor, ...]:
    grouped: dict[str, list[tuple[str, int | None, str | None]]] = {}
    for observation in import_report.observations:
        grouped.setdefault(observation.precursor_id, []).append(
            (
                observation.peptide_sequence,
                observation.precursor_charge,
                observation.protein_ref,
            )
        )
    descriptors: list[_ImportedTargetDescriptor] = []
    for target_id, rows in sorted(grouped.items()):
        descriptors.append(
            _ImportedTargetDescriptor(
                target_id=target_id,
                peptide_sequence=rows[0][0],
                precursor_charge=rows[0][1],
                protein_refs=tuple(sorted({row[2] for row in rows if row[2]})),
            )
        )
    return tuple(descriptors)


def _match_assay_target_ids(
    assay: TargetedValidationPanelAssayInput,
    descriptors: tuple[_ImportedTargetDescriptor, ...],
) -> tuple[str, ...]:
    peptide_matches = [
        descriptor
        for descriptor in descriptors
        if descriptor.peptide_sequence == assay.canonical_peptide
        and descriptor.precursor_charge == assay.precursor_charge
    ]
    if not peptide_matches:
        return ()
    protein_matches = [
        descriptor
        for descriptor in peptide_matches
        if assay.target_protein_ref in descriptor.protein_refs
    ]
    if protein_matches:
        return tuple(sorted(descriptor.target_id for descriptor in protein_matches))
    if assay.uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return ()
    return tuple(sorted(descriptor.target_id for descriptor in peptide_matches))


def _pearson_correlation(
    left_values: list[float], right_values: list[float]
) -> float | None:
    if len(left_values) != len(right_values) or len(left_values) < 2:
        return None
    left_mean = mean(left_values)
    right_mean = mean(right_values)
    left_deltas = [value - left_mean for value in left_values]
    right_deltas = [value - right_mean for value in right_values]
    numerator = sum(
        left * right for left, right in zip(left_deltas, right_deltas, strict=False)
    )
    left_norm = math.sqrt(sum(delta * delta for delta in left_deltas))
    right_norm = math.sqrt(sum(delta * delta for delta in right_deltas))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return numerator / (left_norm * right_norm)


def _format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"
