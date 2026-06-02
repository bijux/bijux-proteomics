# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Laboratory-facing diagnosis of digestion quality and enzyme consistency."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.sequences.digestion import (
    ProteaseCleavageMode,
    ProteaseRule,
    count_missed_cleavages,
    get_protease_rule,
    protease_registry,
)
from bijux_proteomics.lab.protocol_context import DigestionEnzyme
from bijux_proteomics_foundation import JsonModel


class DigestionStatus(StrEnum):
    """Stable sample-level digestion diagnosis outcomes."""

    PASSED = "pass"
    INEFFICIENT_DIGESTION = "inefficient_digestion"
    LOW_SPECIFICITY = "low_specificity"
    ENZYME_MISMATCH = "enzyme_mismatch"


class DigestionPeptideObservation(JsonModel):
    """One peptide observation with enough boundary context for digestion review."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    left_flank: str | None = None
    right_flank: str | None = None
    observation_count: int = Field(default=1, ge=1)

    @field_validator("peptide_sequence")
    @classmethod
    def _normalize_peptide_sequence(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("left_flank", "right_flank")
    @classmethod
    def _normalize_flank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized == "":
            return None
        if len(normalized) != 1:
            raise ValueError("flanking residues must be one residue or null")
        return normalized


class DigestionDiagnosisEntry(JsonModel):
    """One sample-level digestion diagnosis row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)
    semi_specific_rate: float = Field(..., ge=0.0, le=1.0)
    non_specific_rate: float = Field(..., ge=0.0, le=1.0)
    digestion_status: DigestionStatus


class _SpecificityClass(StrEnum):
    ENZYMATIC = "enzymatic"
    SEMI_SPECIFIC = "semi_specific"
    NON_SPECIFIC = "non_specific"


class _DigestionSummary(JsonModel):
    model_config = ConfigDict(extra="forbid")

    missed_cleavage_rate: float = Field(..., ge=0.0, le=1.0)
    semi_specific_rate: float = Field(..., ge=0.0, le=1.0)
    non_specific_rate: float = Field(..., ge=0.0, le=1.0)
    enzymatic_rate: float = Field(..., ge=0.0, le=1.0)
    evidence_score: float


def classify_digestion(
    peptide_table: tuple[DigestionPeptideObservation, ...],
    declared_enzyme: DigestionEnzyme | str,
) -> tuple[DigestionDiagnosisEntry, ...]:
    """Classify sample-level digestion behavior against the declared enzyme."""

    if not peptide_table:
        return ()
    declared_rule = _resolve_declared_rule(declared_enzyme)
    rows_by_sample: dict[str, list[DigestionPeptideObservation]] = {}
    for row in peptide_table:
        rows_by_sample.setdefault(row.sample_id, []).append(row)
    return tuple(
        _diagnose_sample(sample_id, tuple(rows_by_sample[sample_id]), declared_rule)
        for sample_id in sorted(rows_by_sample)
    )


def render_digestion_diagnosis_tsv(
    entries: tuple[DigestionDiagnosisEntry, ...],
) -> str:
    """Render digestion diagnosis rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "missed_cleavage_rate",
            "semi_specific_rate",
            "non_specific_rate",
            "digestion_status",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.sample_id,
                f"{entry.missed_cleavage_rate:.4f}",
                f"{entry.semi_specific_rate:.4f}",
                f"{entry.non_specific_rate:.4f}",
                entry.digestion_status.value,
            )
        )
    return buffer.getvalue()


def _diagnose_sample(
    sample_id: str,
    rows: tuple[DigestionPeptideObservation, ...],
    declared_rule: ProteaseRule,
) -> DigestionDiagnosisEntry:
    declared_summary = _summarize_digestion(rows, declared_rule)
    best_alternative_name, best_alternative_summary = _best_alternative_summary(
        rows,
        declared_rule,
    )

    status = DigestionStatus.PASSED
    specificity_burden = (
        declared_summary.semi_specific_rate + declared_summary.non_specific_rate
    )
    if (
        best_alternative_name is not None
        and best_alternative_summary is not None
        and best_alternative_summary.evidence_score >= declared_summary.evidence_score + 0.2
        and best_alternative_summary.enzymatic_rate >= 0.75
        and (
            declared_summary.missed_cleavage_rate
            >= best_alternative_summary.missed_cleavage_rate + 0.2
            or specificity_burden >= 0.2
        )
    ):
        status = DigestionStatus.ENZYME_MISMATCH
    elif declared_summary.non_specific_rate >= 0.2 or specificity_burden >= 0.25:
        status = DigestionStatus.LOW_SPECIFICITY
    elif declared_summary.missed_cleavage_rate >= 0.25:
        status = DigestionStatus.INEFFICIENT_DIGESTION

    return DigestionDiagnosisEntry(
        sample_id=sample_id,
        missed_cleavage_rate=round(declared_summary.missed_cleavage_rate, 4),
        semi_specific_rate=round(declared_summary.semi_specific_rate, 4),
        non_specific_rate=round(declared_summary.non_specific_rate, 4),
        digestion_status=status,
    )


def _best_alternative_summary(
    rows: tuple[DigestionPeptideObservation, ...],
    declared_rule: ProteaseRule,
) -> tuple[str | None, _DigestionSummary | None]:
    best_name: str | None = None
    best_summary: _DigestionSummary | None = None
    for name, candidate_rule in sorted(protease_registry().items()):
        if candidate_rule.name == declared_rule.name:
            continue
        summary = _summarize_digestion(rows, candidate_rule)
        if best_summary is None or summary.evidence_score > best_summary.evidence_score:
            best_name = name
            best_summary = summary
    return best_name, best_summary


def _summarize_digestion(
    rows: tuple[DigestionPeptideObservation, ...],
    rule: ProteaseRule,
) -> _DigestionSummary:
    total_observations = sum(row.observation_count for row in rows)
    if total_observations <= 0:
        return _DigestionSummary(
            missed_cleavage_rate=0.0,
            semi_specific_rate=0.0,
            non_specific_rate=0.0,
            enzymatic_rate=0.0,
            evidence_score=0.0,
        )

    missed_observations = 0
    semi_specific_observations = 0
    non_specific_observations = 0
    enzymatic_observations = 0
    for row in rows:
        if count_missed_cleavages(row.peptide_sequence, rule) > 0:
            missed_observations += row.observation_count
        specificity = _classify_specificity(row, rule)
        if specificity is _SpecificityClass.ENZYMATIC:
            enzymatic_observations += row.observation_count
        elif specificity is _SpecificityClass.SEMI_SPECIFIC:
            semi_specific_observations += row.observation_count
        else:
            non_specific_observations += row.observation_count

    missed_rate = missed_observations / total_observations
    semi_specific_rate = semi_specific_observations / total_observations
    non_specific_rate = non_specific_observations / total_observations
    enzymatic_rate = enzymatic_observations / total_observations
    evidence_score = round(
        enzymatic_rate
        - (0.6 * missed_rate)
        - (0.8 * semi_specific_rate)
        - (1.2 * non_specific_rate),
        4,
    )
    return _DigestionSummary(
        missed_cleavage_rate=missed_rate,
        semi_specific_rate=semi_specific_rate,
        non_specific_rate=non_specific_rate,
        enzymatic_rate=enzymatic_rate,
        evidence_score=evidence_score,
    )


def _classify_specificity(
    row: DigestionPeptideObservation,
    rule: ProteaseRule,
) -> _SpecificityClass:
    left_valid = _boundary_valid(
        flank=row.left_flank,
        peptide_boundary_residue=row.peptide_sequence[0],
        rule=rule,
        is_left_boundary=True,
    )
    right_valid = _boundary_valid(
        flank=row.right_flank,
        peptide_boundary_residue=row.peptide_sequence[-1],
        rule=rule,
        is_left_boundary=False,
    )
    if left_valid and right_valid:
        return _SpecificityClass.ENZYMATIC
    if left_valid or right_valid:
        return _SpecificityClass.SEMI_SPECIFIC
    return _SpecificityClass.NON_SPECIFIC


def _boundary_valid(
    *,
    flank: str | None,
    peptide_boundary_residue: str,
    rule: ProteaseRule,
    is_left_boundary: bool,
) -> bool:
    if flank is None:
        return True
    if rule.cleavage_mode is ProteaseCleavageMode.C_TERMINAL:
        if is_left_boundary:
            return (
                flank in rule.cleavage_residues
                and peptide_boundary_residue not in rule.blocked_by_next
            )
        return (
            peptide_boundary_residue in rule.cleavage_residues
            and flank not in rule.blocked_by_next
        )
    if is_left_boundary:
        return (
            peptide_boundary_residue in rule.cleavage_residues
            and flank not in rule.blocked_by_previous
        )
    return (
        flank in rule.cleavage_residues
        and peptide_boundary_residue not in rule.blocked_by_previous
    )


def _resolve_declared_rule(declared_enzyme: DigestionEnzyme | str) -> ProteaseRule:
    if isinstance(declared_enzyme, DigestionEnzyme):
        enzyme_name = declared_enzyme.value
    else:
        enzyme_name = declared_enzyme.strip().lower()
    if enzyme_name == DigestionEnzyme.TRYPSIN_LYSC.value:
        enzyme_name = DigestionEnzyme.TRYPSIN.value
    if enzyme_name == DigestionEnzyme.OTHER.value:
        raise ValueError(
            "declared_enzyme='other' is not resolvable for digestion diagnosis"
        )
    return get_protease_rule(enzyme_name)


__all__ = [
    "DigestionDiagnosisEntry",
    "DigestionPeptideObservation",
    "DigestionStatus",
    "classify_digestion",
    "render_digestion_diagnosis_tsv",
]
