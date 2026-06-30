# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed artifact loading and candidate evaluation support for belief audits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.review.claims.result_query_artifacts import (
    _empty_to_none,
    _parse_bool,
    _parse_optional_float,
    _read_tsv_rows,
    _split_multi,
)


@dataclass(frozen=True)
class _RegulatorInferenceArtifact:
    row_id: str
    regulator: str
    evidence_type: str
    signal_surface: str
    source_name: str | None
    source_accession: str | None
    target_count: int
    matched_target_count: int
    coverage_fraction: float
    supporting_protein_refs: tuple[str, ...]
    supporting_site_keys: tuple[str, ...]
    supporting_pathway_ids: tuple[str, ...]
    direction: str | None
    score: float | None
    mean_log2_fold_change: float | None
    mean_activity_score_delta: float | None
    note: str


@dataclass(frozen=True)
class _UnresolvedRegulatorTargetArtifact:
    row_id: str
    regulator: str
    evidence_type: str
    target_field: str
    target_value: str
    source_name: str | None
    source_accession: str | None
    reason: str


@dataclass(frozen=True)
class _ValidationEvidenceCardArtifact:
    candidate_id: str
    candidate_kind: str
    display_label: str
    target_protein_ref: str | None
    site_key: str | None
    discovery_final_score: float | None
    discovery_adjusted_p_value: float | None
    discovery_support_count: int
    biological_role_labels: tuple[str, ...]
    biological_source_ids: tuple[str, ...]
    assay_entry_count: int
    omitted_reason: str | None
    targeted_validation_verdict: str
    targeted_validation_log2_effect: float | None
    confirmed_assay_count: int
    contradicted_assay_count: int
    inconclusive_assay_count: int
    targeted_validation_reason_codes: tuple[str, ...]
    stability_score: float | None
    stability_downgraded: bool
    stability_reason_codes: tuple[str, ...]
    redundancy_dropped: bool
    redundancy_reason_codes: tuple[str, ...]
    final_status: str
    warning_codes: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class _ValidationWarningArtifact:
    warning_id: str
    candidate_id: str
    warning_code: str
    note: str


def _load_regulator_inferences(path: Path) -> tuple[_RegulatorInferenceArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _RegulatorInferenceArtifact(
            row_id=(
                f"{row['regulator']}:{row['evidence_type']}:{row['signal_surface']}:"
                f"{_source_locator(row.get('source_accession', ''), row.get('source_name', ''))}"
            ),
            regulator=row["regulator"],
            evidence_type=row["evidence_type"],
            signal_surface=row["signal_surface"],
            source_name=_empty_to_none(row["source_name"]),
            source_accession=_empty_to_none(row["source_accession"]),
            target_count=int(row["target_count"]),
            matched_target_count=int(row["matched_target_count"]),
            coverage_fraction=_parse_optional_float(row["coverage_fraction"]) or 0.0,
            supporting_protein_refs=_split_multi(row["supporting_protein_refs"]),
            supporting_site_keys=_split_multi(row["supporting_site_keys"]),
            supporting_pathway_ids=_split_multi(row["supporting_pathway_ids"]),
            direction=_empty_to_none(row["direction"]),
            score=_parse_optional_float(row["score"]),
            mean_log2_fold_change=_parse_optional_float(row["mean_log2_fold_change"]),
            mean_activity_score_delta=_parse_optional_float(
                row["mean_activity_score_delta"]
            ),
            note=row["note"],
        )
        for row in rows
    )


def _load_unresolved_regulator_targets(
    path: Path,
) -> tuple[_UnresolvedRegulatorTargetArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _UnresolvedRegulatorTargetArtifact(
            row_id=(
                f"{row['regulator']}:{row['evidence_type']}:{row['target_field']}:"
                f"{row['target_value']}:{_source_locator(row.get('source_accession', ''), row.get('source_name', ''))}"
            ),
            regulator=row["regulator"],
            evidence_type=row["evidence_type"],
            target_field=row["target_field"],
            target_value=row["target_value"],
            source_name=_empty_to_none(row["source_name"]),
            source_accession=_empty_to_none(row["source_accession"]),
            reason=row["reason"],
        )
        for row in rows
    )


def _load_validation_evidence_cards(
    path: Path,
) -> tuple[_ValidationEvidenceCardArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _ValidationEvidenceCardArtifact(
            candidate_id=row["candidate_id"],
            candidate_kind=row["candidate_kind"],
            display_label=row["display_label"],
            target_protein_ref=_empty_to_none(row["target_protein_ref"]),
            site_key=_empty_to_none(row["site_key"]),
            discovery_final_score=_parse_optional_float(row["discovery_final_score"]),
            discovery_adjusted_p_value=_parse_optional_float(
                row["discovery_adjusted_p_value"]
            ),
            discovery_support_count=int(row["discovery_support_count"]),
            biological_role_labels=_split_multi(row["biological_role_labels"]),
            biological_source_ids=_split_multi(row["biological_source_ids"]),
            assay_entry_count=int(row["assay_entry_count"]),
            omitted_reason=_empty_to_none(row["omitted_reason"]),
            targeted_validation_verdict=row["targeted_validation_verdict"],
            targeted_validation_log2_effect=_parse_optional_float(
                row["targeted_validation_log2_effect"]
            ),
            confirmed_assay_count=int(row["confirmed_assay_count"]),
            contradicted_assay_count=int(row["contradicted_assay_count"]),
            inconclusive_assay_count=int(row["inconclusive_assay_count"]),
            targeted_validation_reason_codes=_split_multi(
                row["targeted_validation_reason_codes"]
            ),
            stability_score=_parse_optional_float(row["stability_score"]),
            stability_downgraded=_parse_bool(row["stability_downgraded"]),
            stability_reason_codes=_split_multi(row["stability_reason_codes"]),
            redundancy_dropped=_parse_bool(row["redundancy_dropped"]),
            redundancy_reason_codes=_split_multi(row["redundancy_reason_codes"]),
            final_status=row["final_status"],
            warning_codes=_split_multi(row["warning_codes"]),
            note=row["note"],
        )
        for row in rows
    )


def _load_validation_warnings(path: Path) -> tuple[_ValidationWarningArtifact, ...]:
    rows = _read_tsv_rows(path)
    return tuple(
        _ValidationWarningArtifact(
            warning_id=f"{row['candidate_id']}:{row['warning_code']}",
            candidate_id=row["candidate_id"],
            warning_code=row["warning_code"],
            note=row["note"],
        )
        for row in rows
    )


def _regulator_confidence(entry: _RegulatorInferenceArtifact) -> str:
    if (
        entry.coverage_fraction >= 0.6
        and entry.matched_target_count >= 3
        and (entry.score or 0.0) >= 1.0
    ):
        return "high"
    if entry.coverage_fraction >= 0.3 and entry.matched_target_count >= 2:
        return "moderate"
    if entry.matched_target_count >= 1:
        return "weak"
    return "exploratory"


def _biomarker_confidence(
    card: _ValidationEvidenceCardArtifact,
    warnings: tuple[_ValidationWarningArtifact, ...],
) -> str:
    if (
        card.final_status in {"confirmed", "validated"}
        and not warnings
        and not card.warning_codes
        and not card.stability_downgraded
        and not card.redundancy_dropped
        and card.contradicted_assay_count == 0
    ):
        return "high"
    if card.final_status in {"confirmed", "ready", "retained"}:
        return "moderate"
    if card.final_status in {"blocked", "contradicted", "dropped", "omitted"}:
        return "weak"
    return "exploratory"


def _biomarker_falsifier(card: _ValidationEvidenceCardArtifact) -> str:
    if card.final_status in {"confirmed", "validated", "ready", "retained"}:
        return (
            "Independent targeted assays that reverse the retained effect, fail the "
            "assay-quality review, or reproduce the preserved warning conditions would "
            "falsify this biomarker conclusion."
        )
    return (
        "Independent targeted assays that reproduce the candidate effect without the "
        "preserved contradiction, instability, redundancy, or warning burden would "
        "falsify this current biomarker conclusion."
    )


def _source_locator(source_accession: str, source_name: str) -> str:
    accession = source_accession.strip()
    if accession:
        return accession
    name = source_name.strip()
    if name:
        return name
    return "source"


__all__ = [
    "_RegulatorInferenceArtifact",
    "_UnresolvedRegulatorTargetArtifact",
    "_ValidationEvidenceCardArtifact",
    "_ValidationWarningArtifact",
    "_biomarker_confidence",
    "_biomarker_falsifier",
    "_load_regulator_inferences",
    "_load_unresolved_regulator_targets",
    "_load_validation_evidence_cards",
    "_load_validation_warnings",
    "_regulator_confidence",
]
