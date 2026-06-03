# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned contaminant-aware evidence separation over normalized identification rows."""

from __future__ import annotations

import csv
import hashlib
import io
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics_foundation import JsonModel


class ContaminantSeparatedPsmEntry(JsonModel):
    """One PSM row separated by contaminant evidence posture."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    sample_id: str | None = None
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    intensity: float | None = Field(default=None, ge=0.0)
    contaminant_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    mixed_reference: bool
    pure_contaminant: bool


class ContaminantSeparatedPeptideEntry(JsonModel):
    """One peptide row separated by contaminant evidence posture."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    psm_count: int = Field(..., ge=1)
    contaminant_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    intensity_sum: float = Field(..., ge=0.0)
    mixed_reference: bool
    pure_contaminant: bool


class ContaminantSeparatedProteinEntry(JsonModel):
    """One contaminant protein row with governed supporting burden."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    psm_count: int = Field(..., ge=1)
    peptide_count: int = Field(..., ge=1)
    intensity_sum: float = Field(..., ge=0.0)


class ContaminantBurdenEntry(JsonModel):
    """Contaminant burden summary for one run and optional sample."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    total_psm_count: int = Field(..., ge=0)
    contaminant_psm_count: int = Field(..., ge=0)
    pure_contaminant_psm_count: int = Field(..., ge=0)
    mixed_reference_psm_count: int = Field(..., ge=0)
    contaminant_peptide_count: int = Field(..., ge=0)
    contaminant_protein_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    contaminant_intensity: float = Field(..., ge=0.0)
    contaminant_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    contaminant_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    heavy_contaminant_warning: bool


class ContaminantEvidenceSummary(JsonModel):
    """Compact report-wide contaminant separation summary."""

    model_config = ConfigDict(extra="forbid")

    total_psm_count: int = Field(..., ge=0)
    contaminant_psm_count: int = Field(..., ge=0)
    pure_contaminant_psm_count: int = Field(..., ge=0)
    mixed_reference_psm_count: int = Field(..., ge=0)
    target_only_psm_count: int = Field(..., ge=0)
    contaminant_peptide_count: int = Field(..., ge=0)
    contaminant_protein_count: int = Field(..., ge=0)
    burdened_run_count: int = Field(..., ge=0)
    burdened_sample_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    contaminant_intensity: float = Field(..., ge=0.0)
    contaminant_intensity_fraction: float = Field(..., ge=0.0, le=1.0)


class ContaminantEvidenceReport(JsonModel):
    """Owned contaminant separation report over PSM, peptide, protein, and burden ledgers."""

    model_config = ConfigDict(extra="forbid")

    contaminant_prefixes: tuple[str, ...] = Field(default_factory=tuple)
    warning_psm_fraction: float = Field(..., ge=0.0, le=1.0)
    warning_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    summary: ContaminantEvidenceSummary
    psm_entries: tuple[ContaminantSeparatedPsmEntry, ...] = Field(default_factory=tuple)
    peptide_entries: tuple[ContaminantSeparatedPeptideEntry, ...] = Field(
        default_factory=tuple
    )
    protein_entries: tuple[ContaminantSeparatedProteinEntry, ...] = Field(
        default_factory=tuple
    )
    burden_entries: tuple[ContaminantBurdenEntry, ...] = Field(default_factory=tuple)


def build_contaminant_evidence_report(
    records: tuple[PsmRecord, ...],
    *,
    contaminant_prefixes: tuple[str, ...] = ("CON__",),
    sample_id_by_run: dict[str, str] | None = None,
    warning_psm_fraction: float = 0.1,
    warning_intensity_fraction: float = 0.1,
) -> ContaminantEvidenceReport:
    """Separate contaminant evidence from target evidence across supported ledgers."""
    normalized_prefixes = tuple(
        dict.fromkeys(prefix for prefix in contaminant_prefixes if prefix)
    )
    sample_lookup = sample_id_by_run or {}

    psm_entries: list[ContaminantSeparatedPsmEntry] = []
    peptide_groups: dict[str, list[ContaminantSeparatedPsmEntry]] = {}
    protein_support: dict[str, list[ContaminantSeparatedPsmEntry]] = {}
    burden_groups: dict[tuple[str, str | None], list[ContaminantSeparatedPsmEntry]] = {}
    total_intensity = 0.0
    contaminant_intensity = 0.0

    for record in records:
        run_id = record.run_id or "unassigned"
        sample_id = sample_lookup.get(run_id)
        intensity = record.intensity or 0.0
        total_intensity += intensity
        contaminant_refs = tuple(
            ref
            for ref in record.protein_refs
            if _is_contaminant(ref, normalized_prefixes)
        )
        target_refs = tuple(
            ref for ref in record.protein_refs if ref not in contaminant_refs
        )
        if not contaminant_refs:
            burden_groups.setdefault((run_id, sample_id), []).append(
                ContaminantSeparatedPsmEntry(
                    run_id=run_id,
                    sample_id=sample_id,
                    spectrum_id=record.spectrum_id,
                    canonical_peptide=record.canonical_peptide,
                    score=record.score,
                    q_value=record.q_value,
                    intensity=record.intensity,
                    contaminant_protein_refs=(),
                    target_protein_refs=target_refs,
                    mixed_reference=False,
                    pure_contaminant=False,
                )
            )
            continue

        mixed_reference = bool(target_refs)
        pure_contaminant = not mixed_reference
        contaminant_intensity += intensity
        entry = ContaminantSeparatedPsmEntry(
            run_id=run_id,
            sample_id=sample_id,
            spectrum_id=record.spectrum_id,
            canonical_peptide=record.canonical_peptide,
            score=record.score,
            q_value=record.q_value,
            intensity=record.intensity,
            contaminant_protein_refs=contaminant_refs,
            target_protein_refs=target_refs,
            mixed_reference=mixed_reference,
            pure_contaminant=pure_contaminant,
        )
        psm_entries.append(entry)
        peptide_groups.setdefault(record.canonical_peptide, []).append(entry)
        for protein_ref in contaminant_refs:
            protein_support.setdefault(protein_ref, []).append(entry)
        burden_groups.setdefault((run_id, sample_id), []).append(entry)

    peptide_entries = tuple(
        _build_peptide_entry(peptide, entries)
        for peptide, entries in sorted(peptide_groups.items())
    )
    protein_entries = tuple(
        _build_protein_entry(protein_ref, entries)
        for protein_ref, entries in sorted(protein_support.items())
    )
    burden_entries = tuple(
        _build_burden_entry(
            run_id=run_id,
            sample_id=sample_id,
            entries=entries,
            warning_psm_fraction=warning_psm_fraction,
            warning_intensity_fraction=warning_intensity_fraction,
        )
        for (run_id, sample_id), entries in sorted(
            burden_groups.items(), key=lambda item: (item[0][0], item[0][1] or "")
        )
    )

    payload = {
        "contaminant_prefixes": list(normalized_prefixes),
        "warning_psm_fraction": warning_psm_fraction,
        "warning_intensity_fraction": warning_intensity_fraction,
        "psm_entries": [entry.to_dict() for entry in psm_entries],
        "peptide_entries": [entry.to_dict() for entry in peptide_entries],
        "protein_entries": [entry.to_dict() for entry in protein_entries],
        "burden_entries": [entry.to_dict() for entry in burden_entries],
    }
    contaminant_psm_count = len(psm_entries)
    pure_contaminant_psm_count = sum(
        1 for entry in psm_entries if entry.pure_contaminant
    )
    mixed_reference_psm_count = sum(1 for entry in psm_entries if entry.mixed_reference)
    return ContaminantEvidenceReport(
        contaminant_prefixes=normalized_prefixes,
        warning_psm_fraction=warning_psm_fraction,
        warning_intensity_fraction=warning_intensity_fraction,
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        summary=ContaminantEvidenceSummary(
            total_psm_count=len(records),
            contaminant_psm_count=contaminant_psm_count,
            pure_contaminant_psm_count=pure_contaminant_psm_count,
            mixed_reference_psm_count=mixed_reference_psm_count,
            target_only_psm_count=len(records) - contaminant_psm_count,
            contaminant_peptide_count=len(peptide_entries),
            contaminant_protein_count=len(protein_entries),
            burdened_run_count=len(
                {
                    entry.run_id
                    for entry in burden_entries
                    if entry.heavy_contaminant_warning
                }
            ),
            burdened_sample_count=len(
                {
                    entry.sample_id
                    for entry in burden_entries
                    if entry.sample_id and entry.heavy_contaminant_warning
                }
            ),
            total_intensity=total_intensity,
            contaminant_intensity=contaminant_intensity,
            contaminant_intensity_fraction=_fraction(
                contaminant_intensity, total_intensity
            ),
        ),
        psm_entries=tuple(
            sorted(
                psm_entries, key=lambda entry: (entry.run_id or "", entry.spectrum_id)
            )
        ),
        peptide_entries=peptide_entries,
        protein_entries=protein_entries,
        burden_entries=burden_entries,
    )


def render_contaminant_burden_tsv(report: ContaminantEvidenceReport) -> str:
    """Render run/sample contaminant burden rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "sample_id",
            "total_psm_count",
            "contaminant_psm_count",
            "pure_contaminant_psm_count",
            "mixed_reference_psm_count",
            "contaminant_peptide_count",
            "contaminant_protein_count",
            "total_intensity",
            "contaminant_intensity",
            "contaminant_psm_fraction",
            "contaminant_intensity_fraction",
            "heavy_contaminant_warning",
        )
    )
    for entry in report.burden_entries:
        writer.writerow(
            (
                entry.run_id,
                entry.sample_id or "",
                entry.total_psm_count,
                entry.contaminant_psm_count,
                entry.pure_contaminant_psm_count,
                entry.mixed_reference_psm_count,
                entry.contaminant_peptide_count,
                entry.contaminant_protein_count,
                entry.total_intensity,
                entry.contaminant_intensity,
                entry.contaminant_psm_fraction,
                entry.contaminant_intensity_fraction,
                str(entry.heavy_contaminant_warning).lower(),
            )
        )
    return buffer.getvalue()


def render_contaminant_proteins_tsv(report: ContaminantEvidenceReport) -> str:
    """Render contaminant protein burden rows as TSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_ref",
            "run_ids",
            "sample_ids",
            "psm_count",
            "peptide_count",
            "intensity_sum",
        )
    )
    for entry in report.protein_entries:
        writer.writerow(
            (
                entry.protein_ref,
                ";".join(entry.run_ids),
                ";".join(entry.sample_ids),
                entry.psm_count,
                entry.peptide_count,
                entry.intensity_sum,
            )
        )
    return buffer.getvalue()


def _build_peptide_entry(
    canonical_peptide: str, entries: list[ContaminantSeparatedPsmEntry]
) -> ContaminantSeparatedPeptideEntry:
    contaminant_refs = sorted(
        {ref for entry in entries for ref in entry.contaminant_protein_refs}
    )
    target_refs = sorted(
        {ref for entry in entries for ref in entry.target_protein_refs}
    )
    return ContaminantSeparatedPeptideEntry(
        canonical_peptide=canonical_peptide,
        run_ids=tuple(sorted({entry.run_id for entry in entries if entry.run_id})),
        sample_ids=tuple(
            sorted({entry.sample_id for entry in entries if entry.sample_id})
        ),
        psm_count=len(entries),
        contaminant_protein_refs=tuple(contaminant_refs),
        target_protein_refs=tuple(target_refs),
        intensity_sum=sum(entry.intensity or 0.0 for entry in entries),
        mixed_reference=any(entry.mixed_reference for entry in entries),
        pure_contaminant=all(entry.pure_contaminant for entry in entries),
    )


def _build_protein_entry(
    protein_ref: str, entries: list[ContaminantSeparatedPsmEntry]
) -> ContaminantSeparatedProteinEntry:
    return ContaminantSeparatedProteinEntry(
        protein_ref=protein_ref,
        run_ids=tuple(sorted({entry.run_id for entry in entries if entry.run_id})),
        sample_ids=tuple(
            sorted({entry.sample_id for entry in entries if entry.sample_id})
        ),
        psm_count=len(entries),
        peptide_count=len({entry.canonical_peptide for entry in entries}),
        intensity_sum=sum(entry.intensity or 0.0 for entry in entries),
    )


def _build_burden_entry(
    *,
    run_id: str,
    sample_id: str | None,
    entries: list[ContaminantSeparatedPsmEntry],
    warning_psm_fraction: float,
    warning_intensity_fraction: float,
) -> ContaminantBurdenEntry:
    contaminant_entries = [entry for entry in entries if entry.contaminant_protein_refs]
    total_intensity = sum(entry.intensity or 0.0 for entry in entries)
    contaminant_intensity = sum(entry.intensity or 0.0 for entry in contaminant_entries)
    contaminant_psm_fraction = _fraction(len(contaminant_entries), len(entries))
    contaminant_intensity_fraction = _fraction(contaminant_intensity, total_intensity)
    return ContaminantBurdenEntry(
        run_id=run_id,
        sample_id=sample_id,
        total_psm_count=len(entries),
        contaminant_psm_count=len(contaminant_entries),
        pure_contaminant_psm_count=sum(
            1 for entry in contaminant_entries if entry.pure_contaminant
        ),
        mixed_reference_psm_count=sum(
            1 for entry in contaminant_entries if entry.mixed_reference
        ),
        contaminant_peptide_count=len(
            {entry.canonical_peptide for entry in contaminant_entries}
        ),
        contaminant_protein_count=len(
            {
                ref
                for entry in contaminant_entries
                for ref in entry.contaminant_protein_refs
            }
        ),
        total_intensity=total_intensity,
        contaminant_intensity=contaminant_intensity,
        contaminant_psm_fraction=contaminant_psm_fraction,
        contaminant_intensity_fraction=contaminant_intensity_fraction,
        heavy_contaminant_warning=(
            contaminant_psm_fraction > warning_psm_fraction
            or contaminant_intensity_fraction > warning_intensity_fraction
        ),
    )


def _fraction(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _is_contaminant(protein_ref: str, prefixes: tuple[str, ...]) -> bool:
    return any(protein_ref.startswith(prefix) for prefix in prefixes)


__all__ = [
    "ContaminantBurdenEntry",
    "ContaminantEvidenceReport",
    "ContaminantEvidenceSummary",
    "ContaminantSeparatedPeptideEntry",
    "ContaminantSeparatedProteinEntry",
    "ContaminantSeparatedPsmEntry",
    "build_contaminant_evidence_report",
    "render_contaminant_burden_tsv",
    "render_contaminant_proteins_tsv",
]
