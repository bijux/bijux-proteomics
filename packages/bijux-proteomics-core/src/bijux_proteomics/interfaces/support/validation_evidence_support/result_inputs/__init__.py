# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Validation evidence result loader facade."""

from __future__ import annotations

from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationPanelAssayInput,
)
from .result_entries import (
    _load_validation_evidence_result_assays,
    _load_validation_evidence_results,
)


def _load_targeted_validation_panel_assays(
    path: Path,
) -> tuple[TargetedValidationPanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel assay TSV must include a header row for targeted result validation"
            )
        required_columns = {
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_display_label",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "precursor_charge",
            "selected_transition_count",
            "exported_transition_count",
            "warning_codes",
            "warning_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "panel assay TSV is missing required columns for targeted result validation: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedValidationPanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                warning_codes = tuple(
                    TargetedPanelWarningCode(code)
                    for code in _split_semicolon_field(row.get("warning_codes", ""))
                )
                rows.append(
                    TargetedValidationPanelAssayInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        biomarker_candidate_id=str(
                            row.get("biomarker_candidate_id", "")
                        ).strip(),
                        biomarker_candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("biomarker_candidate_kind", "")).strip()
                        ),
                        biomarker_display_label=str(
                            row.get("biomarker_display_label", "")
                        ).strip(),
                        biomarker_priority_rank=int(
                            str(row.get("biomarker_priority_rank", "")).strip()
                        ),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        warning_codes=warning_codes,
                        warning_note=str(row.get("warning_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid panel assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = [
    "_load_targeted_validation_panel_assays",
    "_load_validation_evidence_result_assays",
    "_load_validation_evidence_results",
]
