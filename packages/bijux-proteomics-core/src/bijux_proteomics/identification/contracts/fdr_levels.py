# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Level-specific and grouped FDR contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.protein_review import (
    PickedProteinFdrEntry,
    calculate_picked_protein_fdr,
)
from bijux_proteomics.identification.contracts.psm import (
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.contracts.score_fdr import (
    FdrEvidenceLevel,
    FdrLevelEntry,
    GroupedFdrBucket,
    GroupedFdrReport,
    NormalizedScoreEntry,
    calculate_basic_target_decoy_fdr,
    normalize_psm_score_orientation,
)

class LevelSpecificFdrReport(JsonModel):
    """Stable report over PSM-, peptide-, and protein-level FDR surfaces."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    psm_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    peptide_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    protein_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class FdrQValueMonotonicityCheck(JsonModel):
    """One monotonicity verification result over an ordered FDR surface."""

    model_config = ConfigDict(extra="forbid")

    scope: str = Field(..., min_length=1)
    entry_count: int = Field(..., ge=0)
    valid: bool
    first_break_rank: int | None = Field(default=None, ge=1)


class FdrQValueMonotonicityReport(JsonModel):
    """Verification report for q-value monotonicity across supported FDR surfaces."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    checks: tuple[FdrQValueMonotonicityCheck, ...] = Field(default_factory=tuple)



class AcceptedPsmProvenanceEntry(JsonModel):
    """Full accepted-PSM provenance row after target-decoy thresholding."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    score_transform: str = Field(..., min_length=1)


class AcceptedPsmProvenanceReport(JsonModel):
    """Accepted PSMs plus the exact policy context that retained them."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    tie_handling: str = Field(..., pattern="^(score_group|stable_record_order)$")
    score_transform: str = Field(..., min_length=1)
    entries: tuple[AcceptedPsmProvenanceEntry, ...] = Field(default_factory=tuple)



def _entity_fdr_entries(
    entities: tuple[tuple[str, float, TargetDecoyLabel, int, tuple[str, ...]], ...],
    *,
    evidence_level: FdrEvidenceLevel,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> tuple[FdrLevelEntry, ...]:
    pseudo_records = tuple(
        PsmRecord(
            spectrum_id=entity_id,
            peptide="A",
            canonical_peptide="A",
            charge=1,
            score=score,
            protein_refs=protein_refs,
            target_decoy_label=label,
        )
        for entity_id, score, label, _member_count, protein_refs in entities
    )
    annotated = calculate_basic_target_decoy_fdr(
        pseudo_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    entity_index = {
        entity_id: (member_count, protein_refs)
        for entity_id, _score, _label, member_count, protein_refs in entities
    }
    return tuple(
        FdrLevelEntry(
            evidence_level=evidence_level,
            entity_id=entry.psm.spectrum_id,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=entity_index[entry.psm.spectrum_id][0],
            protein_refs=entity_index[entry.psm.spectrum_id][1],
        )
        for entry in annotated
    )


def _build_q_value_monotonicity_check(
    *,
    scope: str,
    entries: tuple[FdrLevelEntry, ...] | tuple[PickedProteinFdrEntry, ...],
) -> FdrQValueMonotonicityCheck:
    previous_q_value = -1.0
    first_break_rank: int | None = None
    for entry in entries:
        q_value = entry.q_value
        rank = entry.rank
        if q_value < previous_q_value:
            first_break_rank = rank
            break
        previous_q_value = q_value
    return FdrQValueMonotonicityCheck(
        scope=scope,
        entry_count=len(entries),
        valid=first_break_rank is None,
        first_break_rank=first_break_rank,
    )


def _psm_identity_key(record: PsmRecord) -> tuple[object, ...]:
    return (
        record.spectrum_id,
        record.peptide,
        record.canonical_peptide,
        record.charge,
        record.score,
        record.q_value,
        record.protein_refs,
        record.target_decoy_label.value,
    )


def _score_sorted_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    if score_orientation == "higher_better":
        key_fn = lambda record: (  # noqa: E731
            -record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    else:
        key_fn = lambda record: (  # noqa: E731
            record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    return tuple(sorted(records, key=key_fn))


def build_accepted_psm_provenance_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> AcceptedPsmProvenanceReport:
    """Build accepted-PSM provenance with explicit ranked FDR derivation state."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    normalized_by_identity: dict[tuple[object, ...], list[NormalizedScoreEntry]] = (
        defaultdict(list)
    )
    for record, entry in zip(
        _score_sorted_psm_records(records, score_orientation=score_orientation),
        normalized_entries,
        strict=True,
    ):
        normalized_by_identity[_psm_identity_key(record)].append(entry)

    accepted_entries: list[AcceptedPsmProvenanceEntry] = []
    for annotated_entry in annotated:
        if not annotated_entry.accepted:
            continue
        identity = _psm_identity_key(annotated_entry.psm)
        normalized_entry = normalized_by_identity[identity].pop(0)
        accepted_entries.append(
            AcceptedPsmProvenanceEntry(
                spectrum_id=annotated_entry.psm.spectrum_id,
                peptide=annotated_entry.psm.peptide,
                canonical_peptide=annotated_entry.psm.canonical_peptide,
                charge=annotated_entry.psm.charge,
                protein_refs=annotated_entry.psm.protein_refs,
                target_decoy_label=annotated_entry.psm.target_decoy_label,
                raw_score=annotated_entry.psm.score,
                normalized_score=normalized_entry.normalized_score,
                rank=annotated_entry.rank,
                tie_group_rank=annotated_entry.tie_group_rank,
                tie_group_size=annotated_entry.tie_group_size,
                cumulative_targets=annotated_entry.cumulative_targets,
                cumulative_decoys=annotated_entry.cumulative_decoys,
                fdr=annotated_entry.fdr,
                q_value=annotated_entry.q_value,
                threshold=threshold,
                score_orientation=score_orientation,
                score_transform="rank_normalized_psm_score",
            )
        )
    return AcceptedPsmProvenanceReport(
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        score_transform="rank_normalized_psm_score",
        entries=tuple(accepted_entries),
    )


def calculate_level_specific_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> LevelSpecificFdrReport:
    """Calculate separate PSM-, peptide-, and protein-level FDR surfaces."""
    from bijux_proteomics.identification.peptide_target_decoy_fdr import (
        build_peptide_target_decoy_fdr_report,
    )
    from bijux_proteomics.identification.protein_target_decoy_fdr import (
        build_protein_target_decoy_fdr_report,
    )

    psm_entries = tuple(
        FdrLevelEntry(
            evidence_level=FdrEvidenceLevel.PSM,
            entity_id=entry.psm.spectrum_id,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=1,
            protein_refs=entry.psm.protein_refs,
        )
        for entry in calculate_basic_target_decoy_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            tie_handling="score_group",
            decoy_policy=None,
        )
    )
    peptide_entries = tuple(
        FdrLevelEntry(
            evidence_level=FdrEvidenceLevel.PEPTIDE,
            entity_id=entry.evidence.canonical_peptide,
            score=entry.evidence.best_score,
            q_value=entry.q_value,
            fdr=entry.raw_fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.evidence.target_decoy_label,
            member_count=entry.evidence.psm_count,
            protein_refs=entry.evidence.protein_refs,
        )
        for entry in build_peptide_target_decoy_fdr_report(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            evidence_policy="best_score",
        ).entries
    )
    protein_entries = tuple(
        FdrLevelEntry(
            evidence_level=FdrEvidenceLevel.PROTEIN,
            entity_id=entry.evidence.protein_ref,
            score=entry.evidence.best_score,
            q_value=entry.q_value,
            fdr=entry.raw_fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.evidence.target_decoy_label,
            member_count=entry.evidence.peptide_count,
            protein_refs=(entry.evidence.protein_ref,),
        )
        for entry in build_protein_target_decoy_fdr_report(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            evidence_policy="best_score",
        ).entries
    )
    return LevelSpecificFdrReport(
        score_orientation=score_orientation,
        threshold=threshold,
        psm_entries=psm_entries,
        peptide_entries=peptide_entries,
        protein_entries=protein_entries,
    )


def calculate_grouped_fdr(
    records: tuple[PsmRecord, ...],
    *,
    group_by: str,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> GroupedFdrReport:
    """Calculate grouped FDR over charge state or modification state."""
    if group_by not in {"charge_state", "modification_state"}:
        raise ValueError("group_by must be 'charge_state' or 'modification_state'")
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        group_key = (
            f"z{record.charge}"
            if group_by == "charge_state"
            else ("modified" if "[" in record.canonical_peptide else "unmodified")
        )
        grouped[group_key].append(record)
    buckets = [
        GroupedFdrBucket(
            group_key=group_key,
            entries=tuple(
                FdrLevelEntry(
                    evidence_level=FdrEvidenceLevel.PSM,
                    entity_id=entry.psm.spectrum_id,
                    score=entry.psm.score,
                    q_value=entry.q_value,
                    fdr=entry.fdr,
                    rank=entry.rank,
                    accepted=entry.accepted,
                    target_decoy_label=entry.psm.target_decoy_label,
                    member_count=1,
                    protein_refs=entry.psm.protein_refs,
                )
                for entry in calculate_basic_target_decoy_fdr(
                    tuple(group_records),
                    threshold=threshold,
                    score_orientation=score_orientation,
                    tie_handling="score_group",
                    decoy_policy=None,
                )
            ),
        )
        for group_key, group_records in sorted(grouped.items())
    ]
    return GroupedFdrReport(
        group_by=group_by,
        score_orientation=score_orientation,
        threshold=threshold,
        groups=tuple(buckets),
    )


def verify_fdr_q_value_monotonicity(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> FdrQValueMonotonicityReport:
    """Verify monotonic q-values across supported FDR calculation surfaces."""
    level_report = calculate_level_specific_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    grouped_charge = calculate_grouped_fdr(
        records,
        group_by="charge_state",
        threshold=threshold,
        score_orientation=score_orientation,
    )
    grouped_modification = calculate_grouped_fdr(
        records,
        group_by="modification_state",
        threshold=threshold,
        score_orientation=score_orientation,
    )
    picked = calculate_picked_protein_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    checks = [
        _build_q_value_monotonicity_check(
            scope="psm",
            entries=level_report.psm_entries,
        ),
        _build_q_value_monotonicity_check(
            scope="peptide",
            entries=level_report.peptide_entries,
        ),
        _build_q_value_monotonicity_check(
            scope="protein",
            entries=level_report.protein_entries,
        ),
        *[
            _build_q_value_monotonicity_check(
                scope=f"grouped:{bucket.group_key}",
                entries=bucket.entries,
            )
            for report in (grouped_charge, grouped_modification)
            for bucket in report.groups
        ],
        _build_q_value_monotonicity_check(
            scope="picked_protein",
            entries=picked,
        ),
    ]
    return FdrQValueMonotonicityReport(
        valid=all(check.valid for check in checks),
        checks=tuple(checks),
    )

__all__ = [
    'LevelSpecificFdrReport',
    'FdrQValueMonotonicityCheck',
    'FdrQValueMonotonicityReport',
    'AcceptedPsmProvenanceEntry',
    'AcceptedPsmProvenanceReport',
    'build_accepted_psm_provenance_report',
    'calculate_level_specific_fdr',
    'calculate_grouped_fdr',
    'verify_fdr_q_value_monotonicity',
]
