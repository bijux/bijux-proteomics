# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generate machine-readable falsifiers for analytical claims."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.models.claims import ClaimType, EvidenceClaim


class ClaimFalsifierType(StrEnum):
    """Stable falsifier classes over supported analytical claims."""

    ORTHOGONAL_PROTEIN_QUANT_FAILURE = "orthogonal_protein_quant_failure"
    SITE_LOCALIZATION_OR_CORRECTION_FAILURE = (
        "site_localization_or_correction_failure"
    )
    PATHWAY_MEMBER_SUPPORT_COLLAPSE = "pathway_member_support_collapse"
    REGULATOR_SUBSTRATE_ACTIVITY_COLLAPSE = "regulator_substrate_activity_collapse"
    BIOMARKER_REPLICATION_FAILURE = "biomarker_replication_failure"
    CLAIM_STRUCTURE_GAP = "claim_structure_gap"


class ClaimFalsifierEntry(JsonModel):
    """One falsifier row for one claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    falsifier_type: ClaimFalsifierType
    required_evidence: tuple[str, ...] = Field(default_factory=tuple)
    why_it_matters: str = Field(..., min_length=1)


class ClaimFalsifierSummary(JsonModel):
    """Stable summary over falsifier generation."""

    model_config = ConfigDict(extra="forbid")

    claim_count: int = Field(..., ge=0)
    typed_falsifier_count: int = Field(..., ge=0)
    structure_gap_count: int = Field(..., ge=0)


class ClaimFalsifierReport(JsonModel):
    """Owned falsifier report for one analytical claim."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ClaimFalsifierEntry, ...] = Field(default_factory=tuple)
    summary: ClaimFalsifierSummary
    note: str = Field(..., min_length=1)


def generate_falsifiers(claim: EvidenceClaim) -> ClaimFalsifierReport:
    """Generate a stable falsifier row for one analytical claim."""

    entry = _falsifier_entry(claim)
    return ClaimFalsifierReport(
        entries=(entry,),
        summary=ClaimFalsifierSummary(
            claim_count=1,
            typed_falsifier_count=(
                0 if entry.falsifier_type is ClaimFalsifierType.CLAIM_STRUCTURE_GAP else 1
            ),
            structure_gap_count=(
                1 if entry.falsifier_type is ClaimFalsifierType.CLAIM_STRUCTURE_GAP else 0
            ),
        ),
        note=(
            "falsifier generation keeps each claim challengeable by emitting the "
            "most decision-relevant evidence that would overturn the current "
            "protein, PTM, pathway, regulator, or biomarker interpretation"
        ),
    )


def render_claim_falsifiers_tsv(entries: tuple[ClaimFalsifierEntry, ...]) -> str:
    """Render falsifier rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("claim_id", "falsifier_type", "required_evidence", "why_it_matters"))
    for entry in entries:
        writer.writerow(
            (
                entry.claim_id,
                entry.falsifier_type.value,
                ";".join(entry.required_evidence),
                entry.why_it_matters,
            )
        )
    return handle.getvalue()


def _falsifier_entry(claim: EvidenceClaim) -> ClaimFalsifierEntry:
    target_kind = _target_kind(claim)
    if target_kind == "protein":
        return ClaimFalsifierEntry(
            claim_id=claim.claim_id,
            falsifier_type=ClaimFalsifierType.ORTHOGONAL_PROTEIN_QUANT_FAILURE,
            required_evidence=_required_evidence(
                claim,
                defaults=(
                    "orthogonal protein rerun",
                    "protein-specific peptide support audit",
                    "direction reversal check",
                ),
            ),
            why_it_matters=(
                "Protein claims fall when the retained abundance direction disappears, "
                "reverses, or turns out not to be protein-specific."
            ),
        )
    if target_kind == "ptm_site":
        return ClaimFalsifierEntry(
            claim_id=claim.claim_id,
            falsifier_type=ClaimFalsifierType.SITE_LOCALIZATION_OR_CORRECTION_FAILURE,
            required_evidence=_required_evidence(
                claim,
                defaults=(
                    "site localization rerun",
                    "protein correction rerun",
                    "site-level orthogonal validation",
                ),
            ),
            why_it_matters=(
                "PTM claims depend on durable site localization and a residual site "
                "effect after protein correction, so either failure breaks the claim."
            ),
        )
    if target_kind == "pathway":
        return ClaimFalsifierEntry(
            claim_id=claim.claim_id,
            falsifier_type=ClaimFalsifierType.PATHWAY_MEMBER_SUPPORT_COLLAPSE,
            required_evidence=_required_evidence(
                claim,
                defaults=(
                    "pathway activity rerun",
                    "member overlap confirmation",
                    "pathway confidence recheck",
                ),
            ),
            why_it_matters=(
                "Pathway conclusions are only credible while the retained activity "
                "delta and contributing member support both remain intact."
            ),
        )
    if target_kind == "regulator":
        return ClaimFalsifierEntry(
            claim_id=claim.claim_id,
            falsifier_type=ClaimFalsifierType.REGULATOR_SUBSTRATE_ACTIVITY_COLLAPSE,
            required_evidence=_required_evidence(
                claim,
                defaults=(
                    "substrate panel rerun",
                    "regulator activity consistency check",
                    "matched target coverage review",
                ),
            ),
            why_it_matters=(
                "Regulator claims weaken if the inferred substrate panel no longer "
                "supports one coherent activity direction."
            ),
        )
    if target_kind == "biomarker":
        return ClaimFalsifierEntry(
            claim_id=claim.claim_id,
            falsifier_type=ClaimFalsifierType.BIOMARKER_REPLICATION_FAILURE,
            required_evidence=_required_evidence(
                claim,
                defaults=(
                    "independent cohort replication",
                    "targeted assay confirmation",
                    "assay quality review",
                ),
            ),
            why_it_matters=(
                "Biomarker claims matter only if an independent cohort reproduces the "
                "effect without inheriting the same assay or warning burden."
            ),
        )
    return ClaimFalsifierEntry(
        claim_id=claim.claim_id,
        falsifier_type=ClaimFalsifierType.CLAIM_STRUCTURE_GAP,
        required_evidence=_required_evidence(
            claim,
            defaults=("explicit resolution assay", "typed subject-relation-object claim"),
        ),
        why_it_matters=(
            "A claim without a recognized analytical surface or explicit resolution "
            "assay is not challengeable enough for downstream review."
        ),
    )


def _target_kind(claim: EvidenceClaim) -> str:
    if claim.target_id.startswith("protein:"):
        return "protein"
    if claim.target_id.startswith("ptm_site:"):
        return "ptm_site"
    if claim.target_id.startswith("pathway:"):
        return "pathway"
    if claim.target_id.startswith("regulator:"):
        return "regulator"
    if claim.target_id.startswith("biomarker:") or claim.claim_type is ClaimType.BIOMARKER:
        return "biomarker"
    return "other"


def _required_evidence(
    claim: EvidenceClaim,
    *,
    defaults: tuple[str, ...],
) -> tuple[str, ...]:
    if claim.resolution_assays:
        return tuple(dict.fromkeys((*claim.resolution_assays, *defaults)))
    return defaults


__all__ = [
    "ClaimFalsifierEntry",
    "ClaimFalsifierReport",
    "ClaimFalsifierSummary",
    "ClaimFalsifierType",
    "generate_falsifiers",
    "render_claim_falsifiers_tsv",
]
