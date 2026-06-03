# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Claim-level refusal boundaries for unsupported strong claims."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim

_HIGH_LOCALIZATION_TIERS = {"high", "high_confidence", "localized"}
_FAILED_QC_STATUSES = {"fail", "failed", "invalid"}


class ClaimRefusalReason(StrEnum):
    """Stable reasons for refusing a strong analytical claim."""

    INVALID_DESIGN = "invalid_design"
    FAILED_QC = "failed_qc"
    WEAK_PEPTIDE_SUPPORT = "weak_peptide_support"
    LOW_LOCALIZATION = "low_localization"


class ClaimRefusalThresholds(JsonModel):
    """Machine-readable policy for unsupported-claim refusal."""

    model_config = ConfigDict(extra="forbid")

    minimum_strong_claim_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    minimum_peptide_support_count: int = Field(default=2, ge=1)
    accepted_localization_tiers: tuple[str, ...] = Field(
        default=("high_confidence", "localized"),
        min_length=1,
    )
    require_valid_design: bool = True
    block_failed_qc: bool = True


class ClaimRefusalEntry(JsonModel):
    """One refusal decision over one claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    refused: bool
    refusal_reason: ClaimRefusalReason | None = None
    minimum_missing_evidence: tuple[str, ...] = Field(default_factory=tuple)


class ClaimRefusalSummary(JsonModel):
    """Stable summary over one refusal pass."""

    model_config = ConfigDict(extra="forbid")

    claim_count: int = Field(..., ge=0)
    refused_claim_count: int = Field(..., ge=0)
    invalid_design_count: int = Field(..., ge=0)
    failed_qc_count: int = Field(..., ge=0)
    weak_peptide_support_count: int = Field(..., ge=0)
    low_localization_count: int = Field(..., ge=0)


class ClaimRefusalReport(JsonModel):
    """Owned report for strong-claim refusal decisions."""

    model_config = ConfigDict(extra="forbid")

    thresholds: ClaimRefusalThresholds
    entries: tuple[ClaimRefusalEntry, ...] = Field(default_factory=tuple)
    summary: ClaimRefusalSummary
    note: str = Field(..., min_length=1)


def refuse_unsupported_claims(
    claims: tuple[EvidenceClaim, ...] | list[EvidenceClaim],
    thresholds: ClaimRefusalThresholds | None = None,
) -> ClaimRefusalReport:
    """Refuse strong claims when governed support boundaries are not met."""

    active_thresholds = thresholds or ClaimRefusalThresholds()
    entries = tuple(
        _refusal_entry(claim, thresholds=active_thresholds) for claim in tuple(claims)
    )
    return ClaimRefusalReport(
        thresholds=active_thresholds,
        entries=entries,
        summary=ClaimRefusalSummary(
            claim_count=len(entries),
            refused_claim_count=sum(entry.refused for entry in entries),
            invalid_design_count=sum(
                entry.refusal_reason is ClaimRefusalReason.INVALID_DESIGN
                for entry in entries
            ),
            failed_qc_count=sum(
                entry.refusal_reason is ClaimRefusalReason.FAILED_QC
                for entry in entries
            ),
            weak_peptide_support_count=sum(
                entry.refusal_reason is ClaimRefusalReason.WEAK_PEPTIDE_SUPPORT
                for entry in entries
            ),
            low_localization_count=sum(
                entry.refusal_reason is ClaimRefusalReason.LOW_LOCALIZATION
                for entry in entries
            ),
        ),
        note=(
            "claim refusal keeps strong analytical claims blocked when design "
            "integrity, qc posture, peptide support, or PTM localization does "
            "not meet the minimum governed evidence boundary"
        ),
    )


def render_claim_refusal_tsv(entries: tuple[ClaimRefusalEntry, ...]) -> str:
    """Render claim refusal rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("claim_id", "refused", "refusal_reason", "minimum_missing_evidence")
    )
    for entry in entries:
        writer.writerow(
            (
                entry.claim_id,
                str(entry.refused).lower(),
                "" if entry.refusal_reason is None else entry.refusal_reason.value,
                ";".join(entry.minimum_missing_evidence),
            )
        )
    return handle.getvalue()


def _refusal_entry(
    claim: EvidenceClaim,
    *,
    thresholds: ClaimRefusalThresholds,
) -> ClaimRefusalEntry:
    if claim.confidence < thresholds.minimum_strong_claim_confidence:
        return ClaimRefusalEntry(
            claim_id=claim.claim_id,
            refused=False,
            refusal_reason=None,
            minimum_missing_evidence=(),
        )

    assumption_map = _assumption_map(claim.assumptions)
    design_valid = assumption_map.get("design_valid", "true").lower() == "true"
    if thresholds.require_valid_design and not design_valid:
        return ClaimRefusalEntry(
            claim_id=claim.claim_id,
            refused=True,
            refusal_reason=ClaimRefusalReason.INVALID_DESIGN,
            minimum_missing_evidence=("valid_design",),
        )

    qc_status = assumption_map.get("qc_status", "passed").lower()
    if thresholds.block_failed_qc and qc_status in _FAILED_QC_STATUSES:
        return ClaimRefusalEntry(
            claim_id=claim.claim_id,
            refused=True,
            refusal_reason=ClaimRefusalReason.FAILED_QC,
            minimum_missing_evidence=("passing_qc",),
        )

    peptide_support_count = int(assumption_map.get("peptide_support_count", "0"))
    if peptide_support_count < thresholds.minimum_peptide_support_count:
        return ClaimRefusalEntry(
            claim_id=claim.claim_id,
            refused=True,
            refusal_reason=ClaimRefusalReason.WEAK_PEPTIDE_SUPPORT,
            minimum_missing_evidence=(
                f"peptide_support_count>={thresholds.minimum_peptide_support_count}",
            ),
        )

    if claim.target_id.startswith("ptm_site:"):
        localization_tier = assumption_map.get("localization_tier", "").lower()
        accepted = {tier.lower() for tier in thresholds.accepted_localization_tiers}
        if (
            localization_tier
            and localization_tier not in accepted | _HIGH_LOCALIZATION_TIERS
        ):
            return ClaimRefusalEntry(
                claim_id=claim.claim_id,
                refused=True,
                refusal_reason=ClaimRefusalReason.LOW_LOCALIZATION,
                minimum_missing_evidence=tuple(
                    sorted(set(thresholds.accepted_localization_tiers))
                ),
            )

    return ClaimRefusalEntry(
        claim_id=claim.claim_id,
        refused=False,
        refusal_reason=None,
        minimum_missing_evidence=(),
    )


def _assumption_map(assumptions: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for assumption in assumptions:
        key, separator, value = assumption.partition("=")
        if separator:
            resolved[key.strip()] = value.strip()
    return resolved


__all__ = [
    "ClaimRefusalEntry",
    "ClaimRefusalReason",
    "ClaimRefusalReport",
    "ClaimRefusalSummary",
    "ClaimRefusalThresholds",
    "refuse_unsupported_claims",
    "render_claim_refusal_tsv",
]
