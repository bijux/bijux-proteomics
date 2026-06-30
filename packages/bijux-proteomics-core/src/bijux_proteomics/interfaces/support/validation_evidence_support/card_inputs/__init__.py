# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Validation evidence card input loader facade."""

from __future__ import annotations

from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference.models import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.validation_evidence_cards import (
    ValidationEvidenceOmittedCandidateInput,
    ValidationEvidencePanelAssayInput,
)

from ...targeted_selection_io.field_parsing import _split_semicolon_field
from .discovery_candidates import _load_validation_evidence_discovery_candidates


def _load_validation_evidence_panel_assays(
    path: Path,
) -> tuple[ValidationEvidencePanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel assay TSV must include a header row for validation evidence cards"
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
            "uniqueness_score",
            "precursor_charge",
            "precursor_mz",
            "expected_retention_time_minutes",
            "retention_window_start_minutes",
            "retention_window_end_minutes",
            "selected_transition_count",
            "exported_transition_count",
            "assay_interference_risk_tier",
            "warning_codes",
            "warning_note",
            "source_library_entry_id",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "panel assay TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidencePanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidencePanelAssayInput(
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
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        precursor_mz=float(str(row.get("precursor_mz", "")).strip()),
                        expected_retention_time_minutes=(
                            None
                            if not str(
                                row.get("expected_retention_time_minutes", "")
                            ).strip()
                            else float(
                                str(
                                    row.get("expected_retention_time_minutes", "")
                                ).strip()
                            )
                        ),
                        retention_window_start_minutes=(
                            None
                            if not str(
                                row.get("retention_window_start_minutes", "")
                            ).strip()
                            else float(
                                str(
                                    row.get("retention_window_start_minutes", "")
                                ).strip()
                            )
                        ),
                        retention_window_end_minutes=(
                            None
                            if not str(
                                row.get("retention_window_end_minutes", "")
                            ).strip()
                            else float(
                                str(row.get("retention_window_end_minutes", "")).strip()
                            )
                        ),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        assay_interference_risk_tier=TargetedAssayInterferenceRiskTier(
                            str(row.get("assay_interference_risk_tier", "")).strip()
                        ),
                        warning_codes=tuple(
                            TargetedPanelWarningCode(code)
                            for code in _split_semicolon_field(
                                row.get("warning_codes", "")
                            )
                        ),
                        warning_note=str(row.get("warning_note", "")).strip(),
                        source_library_entry_id=(
                            None
                            if not str(row.get("source_library_entry_id", "")).strip()
                            else str(row.get("source_library_entry_id", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid panel assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_validation_evidence_omitted_candidates(
    path: Path,
) -> tuple[ValidationEvidenceOmittedCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "omitted-candidate TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "omission_reason",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "omitted-candidate TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceOmittedCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceOmittedCandidateInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("candidate_kind", "")).strip()
                        ),
                        display_label=str(row.get("display_label", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        site_key=(
                            None
                            if not str(row.get("site_key", "")).strip()
                            else str(row.get("site_key", "")).strip()
                        ),
                        priority_rank=int(str(row.get("priority_rank", "")).strip()),
                        omission_reason=str(row.get("omission_reason", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid omitted-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = [
    "_load_validation_evidence_discovery_candidates",
    "_load_validation_evidence_omitted_candidates",
    "_load_validation_evidence_panel_assays",
]
