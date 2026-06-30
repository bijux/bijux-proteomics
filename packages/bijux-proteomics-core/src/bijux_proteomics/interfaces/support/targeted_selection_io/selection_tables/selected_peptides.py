# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Selected-peptide TSV loading for targeted transition selection."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from ...imports import (
    DiscoveryTargetedPeptideSelectionEntry,
    PeptideChemicalLiabilityTier,
    PeptideDetectabilityTier,
    PeptideEvidenceClass,
    PeptideUniquenessClass,
    TargetedPeptideCandidateSource,
)

from ..field_parsing import _parse_cli_bool, _split_semicolon_field


def _load_selected_targeted_peptides(
    path: Path,
) -> tuple[DiscoveryTargetedPeptideSelectionEntry, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "selected-peptide TSV must include a header row for targeted transition selection"
            )
        required_columns = {
            "target_protein_ref",
            "target_protein_group_id",
            "rank",
            "candidate_source",
            "peptide_sequence",
            "canonical_peptide",
            "observed_in_discovery",
            "uniqueness_class",
            "uniqueness_score",
            "detectability_score",
            "detectability_tier",
            "suitability_score",
            "liability_tier",
            "selection_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "selected-peptide TSV is missing required columns for targeted transition selection: "
                + ", ".join(sorted(missing_columns))
            )
        entries: list[DiscoveryTargetedPeptideSelectionEntry] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                primary_evidence_class_raw = str(
                    row.get("primary_evidence_class", "")
                ).strip()
                entries.append(
                    DiscoveryTargetedPeptideSelectionEntry(
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            value
                            if (value := str(row.get("gene_symbol", "")).strip())
                            else None
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        candidate_source=TargetedPeptideCandidateSource(
                            str(row.get("candidate_source", "")).strip()
                        ),
                        rank=int(str(row.get("rank", "")).strip()),
                        observed_in_discovery=_parse_cli_bool(
                            row.get("observed_in_discovery", ""),
                            field_name="observed_in_discovery",
                        ),
                        observed_psm_count=(
                            None
                            if not str(row.get("observed_psm_count", "")).strip()
                            else int(str(row.get("observed_psm_count", "")).strip())
                        ),
                        run_count=(
                            None
                            if not str(row.get("run_count", "")).strip()
                            else int(str(row.get("run_count", "")).strip())
                        ),
                        detection_frequency=(
                            None
                            if not str(row.get("detection_frequency", "")).strip()
                            else float(str(row.get("detection_frequency", "")).strip())
                        ),
                        replicate_consistency=(
                            None
                            if not str(row.get("replicate_consistency", "")).strip()
                            else float(
                                str(row.get("replicate_consistency", "")).strip()
                            )
                        ),
                        primary_evidence_class=(
                            None
                            if not primary_evidence_class_raw
                            else PeptideEvidenceClass(primary_evidence_class_raw)
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        detectability_score=float(
                            str(row.get("detectability_score", "")).strip()
                        ),
                        detectability_tier=PeptideDetectabilityTier(
                            str(row.get("detectability_tier", "")).strip()
                        ),
                        suitability_score=float(
                            str(row.get("suitability_score", "")).strip()
                        ),
                        liability_tier=PeptideChemicalLiabilityTier(
                            str(row.get("liability_tier", "")).strip()
                        ),
                        liability_codes=_split_semicolon_field(
                            row.get("liability_codes", "")
                        ),
                        selection_score=float(
                            str(row.get("selection_score", "")).strip()
                        ),
                        selection_reasons=_split_semicolon_field(
                            row.get("selection_reasons", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid selected-peptide row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(entries)


__all__ = ("_load_selected_targeted_peptides",)
