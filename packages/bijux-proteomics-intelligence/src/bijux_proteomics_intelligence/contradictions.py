# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pairwise contradiction detection over analytical claims."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from itertools import combinations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim

_STRONG_EFFECT_THRESHOLD = 1.0
_CORRECTED_SITE_STATUSES = {
    "corrected",
    "high_confidence_corrected",
    "corrected_low_localization",
}
_UNCORRECTED_SITE_STATUSES = {
    "uncorrected",
    "not_requested",
    "missing_protein_baseline",
}


class ClaimContradictionType(StrEnum):
    """Stable pairwise claim-relationship outcomes."""

    DIRECT_OPPOSITION = "direct_opposition"
    CONTRADICTION_GROUP = "contradiction_group"
    PROTEIN_SITE_CONTRADICTION = "protein_site_contradiction"
    SITE_SPECIFIC = "site_specific"


class ClaimContradictionSeverity(StrEnum):
    """Stable severity scale over contradiction rows."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ClaimContradictionEntry(JsonModel):
    """One stable claim-pair contradiction row."""

    model_config = ConfigDict(extra="forbid")

    claim_a: str = Field(..., min_length=1)
    claim_b: str = Field(..., min_length=1)
    contradiction_type: ClaimContradictionType
    severity: ClaimContradictionSeverity
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ClaimContradictionSummary(JsonModel):
    """Stable summary over pairwise claim contradictions."""

    model_config = ConfigDict(extra="forbid")

    pair_count: int = Field(..., ge=0)
    direct_opposition_count: int = Field(..., ge=0)
    contradiction_group_count: int = Field(..., ge=0)
    protein_site_contradiction_count: int = Field(..., ge=0)
    site_specific_count: int = Field(..., ge=0)
    high_severity_count: int = Field(..., ge=0)


class ClaimContradictionReport(JsonModel):
    """Owned contradiction report over analytical claims."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ClaimContradictionEntry, ...] = Field(default_factory=tuple)
    summary: ClaimContradictionSummary
    note: str = Field(..., min_length=1)


def find_claim_contradictions(
    claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
) -> ClaimContradictionReport:
    """Detect pairwise contradictions and site-specific PTM exceptions."""

    claim_items = tuple(claims)
    claim_ids: set[str] = set()
    for claim in claim_items:
        if claim.claim_id in claim_ids:
            raise ValueError("claim contradiction detection requires unique claim_id rows")
        claim_ids.add(claim.claim_id)

    entries: list[ClaimContradictionEntry] = []
    for left, right in combinations(claim_items, 2):
        entry = _classify_claim_pair(left, right)
        if entry is not None:
            entries.append(entry)

    stable_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.claim_a,
                entry.claim_b,
                entry.contradiction_type.value,
            ),
        )
    )
    return ClaimContradictionReport(
        entries=stable_entries,
        summary=ClaimContradictionSummary(
            pair_count=len(stable_entries),
            direct_opposition_count=sum(
                1
                for entry in stable_entries
                if entry.contradiction_type is ClaimContradictionType.DIRECT_OPPOSITION
            ),
            contradiction_group_count=sum(
                1
                for entry in stable_entries
                if entry.contradiction_type is ClaimContradictionType.CONTRADICTION_GROUP
            ),
            protein_site_contradiction_count=sum(
                1
                for entry in stable_entries
                if entry.contradiction_type
                is ClaimContradictionType.PROTEIN_SITE_CONTRADICTION
            ),
            site_specific_count=sum(
                1
                for entry in stable_entries
                if entry.contradiction_type is ClaimContradictionType.SITE_SPECIFIC
            ),
            high_severity_count=sum(
                1
                for entry in stable_entries
                if entry.severity is ClaimContradictionSeverity.HIGH
            ),
        ),
        note=(
            "claim contradiction detection keeps direct disagreements explicit while "
            "treating protein-unchanged and PTM-shifted pairs as site-specific only "
            "when correction evidence preserves a residual site effect after protein "
            "abundance adjustment"
        ),
    )


def render_claim_contradictions_tsv(
    entries: tuple[ClaimContradictionEntry, ...],
) -> str:
    """Render claim contradiction rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("claim_a", "claim_b", "contradiction_type", "severity", "evidence_ids"))
    for entry in entries:
        writer.writerow(
            (
                entry.claim_a,
                entry.claim_b,
                entry.contradiction_type.value,
                entry.severity.value,
                ";".join(entry.evidence_ids),
            )
        )
    return handle.getvalue()


def _classify_claim_pair(
    left: EvidenceClaim,
    right: EvidenceClaim,
) -> ClaimContradictionEntry | None:
    if not _same_condition_scope(left, right):
        return None

    protein_site_entry = _classify_protein_ptm_pair(left, right)
    if protein_site_entry is not None:
        return protein_site_entry

    if (
        left.contradiction_group
        and left.contradiction_group == right.contradiction_group
        and _claims_disagree(left, right)
    ):
        return _build_entry(
            left,
            right,
            contradiction_type=ClaimContradictionType.CONTRADICTION_GROUP,
            severity=ClaimContradictionSeverity.HIGH,
        )

    if left.target_id == right.target_id and _claims_disagree(left, right):
        return _build_entry(
            left,
            right,
            contradiction_type=ClaimContradictionType.DIRECT_OPPOSITION,
            severity=ClaimContradictionSeverity.HIGH,
        )

    return None


def _classify_protein_ptm_pair(
    left: EvidenceClaim,
    right: EvidenceClaim,
) -> ClaimContradictionEntry | None:
    left_kind = _target_kind(left.target_id)
    right_kind = _target_kind(right.target_id)
    if {left_kind, right_kind} != {"protein", "ptm_site"}:
        return None

    protein_claim = left if left_kind == "protein" else right
    ptm_claim = right if protein_claim is left else left
    protein_id = _protein_id_from_target(protein_claim.target_id)
    site_protein_id = _protein_id_from_target(ptm_claim.target_id)
    if protein_id is None or protein_id != site_protein_id:
        return None

    protein_direction = _normalized_direction(protein_claim.direction)
    ptm_direction = _normalized_direction(ptm_claim.direction)
    if protein_direction != "neutral" or ptm_direction not in {"up", "down"}:
        return None
    if not _is_strong_change(ptm_claim):
        return None

    correction_assumptions = _assumption_map(ptm_claim.assumptions)
    correction_status = correction_assumptions.get("protein_correction_status")
    mechanism_class = correction_assumptions.get("mechanism_class")
    mechanism_reason_code = correction_assumptions.get("mechanism_reason_code")
    if (
        correction_status in _CORRECTED_SITE_STATUSES
        and (
            mechanism_class == "site_specific"
            or mechanism_reason_code == "residual_site_effect_after_correction"
        )
    ):
        severity = (
            ClaimContradictionSeverity.MODERATE
            if correction_status == "corrected_low_localization"
            else ClaimContradictionSeverity.LOW
        )
        return _build_entry(
            left,
            right,
            contradiction_type=ClaimContradictionType.SITE_SPECIFIC,
            severity=severity,
        )

    if correction_status in _UNCORRECTED_SITE_STATUSES or correction_status is None:
        return _build_entry(
            left,
            right,
            contradiction_type=ClaimContradictionType.PROTEIN_SITE_CONTRADICTION,
            severity=ClaimContradictionSeverity.HIGH,
        )

    return _build_entry(
        left,
        right,
        contradiction_type=ClaimContradictionType.PROTEIN_SITE_CONTRADICTION,
        severity=ClaimContradictionSeverity.MODERATE,
    )


def _build_entry(
    left: EvidenceClaim,
    right: EvidenceClaim,
    *,
    contradiction_type: ClaimContradictionType,
    severity: ClaimContradictionSeverity,
) -> ClaimContradictionEntry:
    claim_a, claim_b = sorted((left.claim_id, right.claim_id))
    evidence_ids = tuple(
        sorted(
            {
                *left.evidence_ids,
                *left.contradicting_evidence_ids,
                *right.evidence_ids,
                *right.contradicting_evidence_ids,
            }
        )
    )
    return ClaimContradictionEntry(
        claim_a=claim_a,
        claim_b=claim_b,
        contradiction_type=contradiction_type,
        severity=severity,
        evidence_ids=evidence_ids,
    )


def _same_condition_scope(left: EvidenceClaim, right: EvidenceClaim) -> bool:
    return (
        left.condition is None
        or right.condition is None
        or left.condition == right.condition
    )


def _claims_disagree(left: EvidenceClaim, right: EvidenceClaim) -> bool:
    left_direction = _normalized_direction(left.direction)
    right_direction = _normalized_direction(right.direction)
    if left_direction == "unknown" or right_direction == "unknown":
        return left.polarity != right.polarity
    if left_direction != right_direction:
        return True
    return left.polarity != right.polarity


def _normalized_direction(direction: str | None) -> str:
    if direction is None:
        return "unknown"
    normalized = direction.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {
        "increase",
        "increases",
        "increased",
        "up",
        "higher",
        "rise",
        "rises",
        "rising",
        "activation",
        "activated",
    }:
        return "up"
    if normalized in {
        "decrease",
        "decreases",
        "decreased",
        "down",
        "lower",
        "loss",
        "reduced",
        "inhibition",
        "inhibited",
    }:
        return "down"
    if normalized in {
        "unchanged",
        "no_change",
        "not_changed",
        "stable",
        "neutral",
    }:
        return "neutral"
    return "unknown"


def _is_strong_change(claim: EvidenceClaim) -> bool:
    return claim.magnitude is not None and abs(claim.magnitude) >= _STRONG_EFFECT_THRESHOLD


def _target_kind(target_id: str) -> str:
    if target_id.startswith("protein:"):
        return "protein"
    if target_id.startswith("ptm_site:"):
        return "ptm_site"
    return "other"


def _protein_id_from_target(target_id: str) -> str | None:
    if target_id.startswith("protein:"):
        _, protein_id = target_id.split(":", 1)
        return protein_id
    if target_id.startswith("ptm_site:"):
        parts = target_id.split(":")
        if len(parts) >= 3:
            return parts[1]
    return None


def _assumption_map(assumptions: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for assumption in assumptions:
        key, separator, value = assumption.partition("=")
        if separator:
            resolved[key.strip()] = value.strip()
    return resolved


__all__ = [
    "ClaimContradictionEntry",
    "ClaimContradictionReport",
    "ClaimContradictionSeverity",
    "ClaimContradictionSummary",
    "ClaimContradictionType",
    "find_claim_contradictions",
    "render_claim_contradictions_tsv",
]
