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
)

from ...targeted_selection_io.field_parsing import _split_semicolon_field
from .discovery_candidates import _load_validation_evidence_discovery_candidates
from .panel_assays import _load_validation_evidence_panel_assays


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
