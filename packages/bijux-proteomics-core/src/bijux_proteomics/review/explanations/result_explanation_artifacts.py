# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Artifact loading and lookup support for deterministic result explanations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.review.claims.result_query_artifacts import (
    _empty_to_none,
    _load_result_artifact_context,
    _node_ids_for_entity,
    _parse_bool,
    _parse_optional_float,
    _QcRunArtifact,
    _read_tsv_rows,
    _ResultArtifactContext,
    _sample_to_failed_qc_runs,
    _split_multi,
)


@dataclass(frozen=True)
class _PathwayComparisonArtifact:
    comparison_row_id: str
    pathway_id: str
    pathway_name: str | None
    source_name: str | None
    source_accession: str | None
    condition_a: str
    condition_b: str
    condition_a_confidence_status: str
    condition_b_confidence_status: str
    comparison_confidence_status: str
    mean_activity_score_a: float | None
    mean_activity_score_b: float | None
    activity_score_delta: float | None


@dataclass(frozen=True)
class _PathwayMemberContributionArtifact:
    pathway_id: str
    member_id: str
    observed_protein_refs: tuple[str, ...]
    member_activity_score: float | None
    observed: bool


@dataclass(frozen=True)
class _PathwayUnresolvedMemberArtifact:
    pathway_id: str
    member_id: str
    reason: str


@dataclass(frozen=True)
class _RejectedClaimArtifact:
    claim_id: str
    claim_kind: str
    subject_id: str
    subject_label: str
    claim_text: str
    condition_a: str
    condition_b: str
    asserted_direction: str
    adjusted_p_value: float | None
    effect_size: float | None
    robustness_score: float | None
    imputation_dependent: bool
    evidence_tier: str | None
    confidence_tier: str | None
    pathway_confidence_status: str | None
    pathway_delta: float | None
    regulator_evidence_type: str | None
    regulator_signal_surface: str | None
    regulator_score: float | None
    reason_codes: tuple[str, ...]
    source_ids: tuple[str, ...]
    validation_note: str


@dataclass(frozen=True)
class _RejectedClaimLookupIndex:
    claims_by_claim_id: dict[str, _RejectedClaimArtifact]
    claims_by_subject_id: dict[str, tuple[_RejectedClaimArtifact, ...]]
    claims_by_subject_label: dict[str, tuple[_RejectedClaimArtifact, ...]]


@dataclass(frozen=True)
class _ResultExplanationArtifactContext:
    base_context: _ResultArtifactContext
    pathway_comparisons: tuple[_PathwayComparisonArtifact, ...]
    pathway_member_contributions: tuple[_PathwayMemberContributionArtifact, ...]
    pathway_unresolved_members: tuple[_PathwayUnresolvedMemberArtifact, ...]
    rejected_claims: tuple[_RejectedClaimArtifact, ...]
    rejected_claim_index: _RejectedClaimLookupIndex
    biological_report_available: bool
    ptm_report_available: bool
    pathway_activity_available: bool
    rejected_claims_available: bool
    qc_available: bool


def _load_result_explanation_artifact_context(
    *,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> _ResultExplanationArtifactContext:
    base_context = _load_result_artifact_context(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    pathway_comparison_path = (
        None
        if biological_report_dir is None
        else biological_report_dir / "biological_pathway_activity_condition_comparisons.tsv"
    )
    pathway_member_path = (
        None
        if biological_report_dir is None
        else biological_report_dir / "biological_pathway_activity_members.tsv"
    )
    pathway_unresolved_path = (
        None
        if biological_report_dir is None
        else biological_report_dir / "biological_pathway_activity_unresolved.tsv"
    )
    rejected_claims_path = (
        None
        if biological_report_dir is None
        else biological_report_dir / "biological_rejected_claims.tsv"
    )
    pathway_comparisons = (
        ()
        if pathway_comparison_path is None or not pathway_comparison_path.exists()
        else _load_pathway_comparisons(pathway_comparison_path)
    )
    pathway_member_contributions = (
        ()
        if pathway_member_path is None or not pathway_member_path.exists()
        else _load_pathway_member_contributions(pathway_member_path)
    )
    pathway_unresolved_members = (
        ()
        if pathway_unresolved_path is None or not pathway_unresolved_path.exists()
        else _load_pathway_unresolved_members(pathway_unresolved_path)
    )
    rejected_claims = (
        ()
        if rejected_claims_path is None or not rejected_claims_path.exists()
        else _load_rejected_claims(rejected_claims_path)
    )
    return _ResultExplanationArtifactContext(
        base_context=base_context,
        pathway_comparisons=pathway_comparisons,
        pathway_member_contributions=pathway_member_contributions,
        pathway_unresolved_members=pathway_unresolved_members,
        rejected_claims=rejected_claims,
        rejected_claim_index=_build_rejected_claim_lookup_index(rejected_claims),
        biological_report_available=biological_report_dir is not None,
        ptm_report_available=ptm_report_dir is not None,
        pathway_activity_available=bool(pathway_comparisons),
        rejected_claims_available=bool(rejected_claims),
        qc_available=bool(run_qc_assessment_tsv_paths),
    )


def _load_pathway_comparisons(path: Path) -> tuple[_PathwayComparisonArtifact, ...]:
    return tuple(
        _PathwayComparisonArtifact(
            comparison_row_id=f"{row['pathway_id']}:{row['condition_a']}:{row['condition_b']}",
            pathway_id=row["pathway_id"],
            pathway_name=_empty_to_none(row.get("pathway_name")),
            source_name=_empty_to_none(row.get("source_name")),
            source_accession=_empty_to_none(row.get("source_accession")),
            condition_a=row["condition_a"],
            condition_b=row["condition_b"],
            condition_a_confidence_status=row["condition_a_confidence_status"],
            condition_b_confidence_status=row["condition_b_confidence_status"],
            comparison_confidence_status=row["comparison_confidence_status"],
            mean_activity_score_a=_parse_optional_float(
                row.get("mean_activity_score_a", "")
            ),
            mean_activity_score_b=_parse_optional_float(
                row.get("mean_activity_score_b", "")
            ),
            activity_score_delta=_parse_optional_float(
                row.get("activity_score_delta", "")
            ),
        )
        for row in _read_tsv_rows(path)
    )


def _load_pathway_member_contributions(
    path: Path,
) -> tuple[_PathwayMemberContributionArtifact, ...]:
    return tuple(
        _PathwayMemberContributionArtifact(
            pathway_id=row["pathway_id"],
            member_id=row["member_id"],
            observed_protein_refs=_split_multi(row.get("observed_protein_refs", "")),
            member_activity_score=_parse_optional_float(
                row.get("member_activity_score", "")
            ),
            observed=_parse_bool(row.get("observed", "")),
        )
        for row in _read_tsv_rows(path)
    )


def _load_pathway_unresolved_members(
    path: Path,
) -> tuple[_PathwayUnresolvedMemberArtifact, ...]:
    return tuple(
        _PathwayUnresolvedMemberArtifact(
            pathway_id=row["pathway_id"],
            member_id=row["member_id"],
            reason=row["reason"],
        )
        for row in _read_tsv_rows(path)
    )


def _load_rejected_claims(path: Path) -> tuple[_RejectedClaimArtifact, ...]:
    return tuple(
        _RejectedClaimArtifact(
            claim_id=row["claim_id"],
            claim_kind=row["claim_kind"],
            subject_id=row["subject_id"],
            subject_label=row["subject_label"],
            claim_text=row["claim_text"],
            condition_a=row["condition_a"],
            condition_b=row["condition_b"],
            asserted_direction=row["asserted_direction"],
            adjusted_p_value=_parse_optional_float(row.get("adjusted_p_value", "")),
            effect_size=_parse_optional_float(row.get("effect_size", "")),
            robustness_score=_parse_optional_float(row.get("robustness_score", "")),
            imputation_dependent=_parse_bool(row.get("imputation_dependent", "")),
            evidence_tier=_empty_to_none(row.get("evidence_tier")),
            confidence_tier=_empty_to_none(row.get("confidence_tier")),
            pathway_confidence_status=_empty_to_none(
                row.get("pathway_confidence_status")
            ),
            pathway_delta=_parse_optional_float(row.get("pathway_delta", "")),
            regulator_evidence_type=_empty_to_none(
                row.get("regulator_evidence_type")
            ),
            regulator_signal_surface=_empty_to_none(
                row.get("regulator_signal_surface")
            ),
            regulator_score=_parse_optional_float(row.get("regulator_score", "")),
            reason_codes=_split_multi(row.get("reason_codes", "")),
            source_ids=_split_multi(row.get("source_ids", "")),
            validation_note=row["validation_note"],
        )
        for row in _read_tsv_rows(path)
    )


def _build_rejected_claim_lookup_index(
    claims: tuple[_RejectedClaimArtifact, ...],
) -> _RejectedClaimLookupIndex:
    claims_by_claim_id = {claim.claim_id: claim for claim in claims}
    claims_by_subject_id: dict[str, list[_RejectedClaimArtifact]] = {}
    claims_by_subject_label: dict[str, list[_RejectedClaimArtifact]] = {}
    for claim in claims:
        claims_by_subject_id.setdefault(claim.subject_id, []).append(claim)
        claims_by_subject_label.setdefault(claim.subject_label, []).append(claim)
    return _RejectedClaimLookupIndex(
        claims_by_claim_id=claims_by_claim_id,
        claims_by_subject_id={
            subject_id: tuple(entries)
            for subject_id, entries in claims_by_subject_id.items()
        },
        claims_by_subject_label={
            subject_label: tuple(entries)
            for subject_label, entries in claims_by_subject_label.items()
        },
    )


def _find_pathway_comparison(
    pathway_comparisons: tuple[_PathwayComparisonArtifact, ...],
    subject_id: str | None,
) -> _PathwayComparisonArtifact | None:
    if subject_id is None:
        return None
    for comparison in pathway_comparisons:
        if comparison.comparison_row_id == subject_id:
            return comparison
        if comparison.pathway_id == subject_id:
            return comparison
        if comparison.pathway_name and comparison.pathway_name == subject_id:
            return comparison
        if comparison.source_accession and comparison.source_accession == subject_id:
            return comparison
    return None


def _top_pathway_members(
    pathway_member_contributions: tuple[_PathwayMemberContributionArtifact, ...],
    pathway_id: str,
) -> tuple[str, ...]:
    members = [
        member
        for member in pathway_member_contributions
        if member.pathway_id == pathway_id and member.observed
    ]
    members.sort(
        key=lambda member: (
            member.member_activity_score is None,
            0.0
            if member.member_activity_score is None
            else -abs(member.member_activity_score),
            member.member_id,
        )
    )
    labels = [
        member.member_id
        if not member.observed_protein_refs
        else f"{member.member_id} ({','.join(member.observed_protein_refs)})"
        for member in members[:3]
    ]
    return tuple(labels)


def _pathway_unresolved_members(
    pathway_unresolved_members: tuple[_PathwayUnresolvedMemberArtifact, ...],
    pathway_id: str,
) -> tuple[_PathwayUnresolvedMemberArtifact, ...]:
    return tuple(
        member for member in pathway_unresolved_members if member.pathway_id == pathway_id
    )


def _find_failed_qc_run(
    context: _ResultArtifactContext,
    sample_id: str | None,
) -> _QcRunArtifact | None:
    if sample_id is None:
        return None
    return next(
        (
            entry
            for entry in context.qc_runs
            if entry.qc_status == "fail" and entry.run_id == sample_id
        ),
        None,
    )


def _find_rejected_claim(
    rejected_claim_index: _RejectedClaimLookupIndex,
    subject_id: str | None,
) -> _RejectedClaimArtifact | None:
    if subject_id is None:
        return None
    direct = rejected_claim_index.claims_by_claim_id.get(subject_id)
    if direct is not None:
        return direct
    by_subject_id = rejected_claim_index.claims_by_subject_id.get(subject_id, ())
    if by_subject_id:
        return by_subject_id[0]
    by_label = rejected_claim_index.claims_by_subject_label.get(subject_id, ())
    if by_label:
        return by_label[0]
    return None

def _rejected_claim_graph_node_ids(
    claim: _RejectedClaimArtifact,
    context: _ResultArtifactContext,
) -> tuple[str, ...]:
    if claim.claim_kind == "protein_abundance_change":
        return _node_ids_for_entity(
            context.graph_node_index,
            entity_type="protein",
            entity_ref=claim.subject_id,
        )
    if claim.claim_kind == "pathway_activity_change":
        return _node_ids_for_entity(
            context.graph_node_index,
            entity_type="pathway",
            entity_ref=claim.subject_id,
        )
    return ()


def _rejected_claim_signal_summary(claim: _RejectedClaimArtifact) -> str:
    if claim.claim_kind == "pathway_activity_change":
        return (
            "pathway delta is "
            f"{_format_float(claim.pathway_delta)} with confidence "
            f"{claim.pathway_confidence_status or 'unknown'}"
        )
    if claim.claim_kind == "regulator_activity_change":
        return (
            "regulator score is "
            f"{_format_float(claim.regulator_score)} from "
            f"{claim.regulator_signal_surface or 'unknown'}"
        )
    return "candidate carried source evidence but still failed validation checks"


def _format_float(value: float | None) -> str:
    return "not available" if value is None else f"{value:.4g}"


__all__ = [
    "_PathwayComparisonArtifact",
    "_PathwayMemberContributionArtifact",
    "_PathwayUnresolvedMemberArtifact",
    "_RejectedClaimArtifact",
    "_RejectedClaimLookupIndex",
    "_ResultExplanationArtifactContext",
    "_build_rejected_claim_lookup_index",
    "_find_failed_qc_run",
    "_find_pathway_comparison",
    "_find_rejected_claim",
    "_load_pathway_comparisons",
    "_load_pathway_member_contributions",
    "_load_pathway_unresolved_members",
    "_load_rejected_claims",
    "_load_result_explanation_artifact_context",
    "_pathway_unresolved_members",
    "_rejected_claim_graph_node_ids",
    "_rejected_claim_signal_summary",
    "_top_pathway_members",
]
