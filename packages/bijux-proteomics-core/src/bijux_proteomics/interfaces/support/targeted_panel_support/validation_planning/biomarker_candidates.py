# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biomarker-candidate TSV loading for validation planning entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.validation_planning import (
    ValidationPlanningBiomarkerCandidateInput,
)

from ...targeted_selection_io.field_parsing import _split_semicolon_field


def _load_validation_planning_biomarker_candidates(
    path: Path,
) -> tuple[ValidationPlanningBiomarkerCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for validation planning"
            )
        required_columns = {
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "penalty_total",
            "uncertainty",
            "effect_size",
            "adjusted_p_value",
            "support_count",
            "robustness_score",
            "assay_feasibility_score",
            "rank_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningBiomarkerCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningBiomarkerCandidateInput(
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
                        final_score=float(str(row.get("final_score", "")).strip()),
                        penalty_total=float(str(row.get("penalty_total", "")).strip()),
                        uncertainty=float(str(row.get("uncertainty", "")).strip()),
                        effect_size=(
                            None
                            if not str(row.get("effect_size", "")).strip()
                            else float(str(row.get("effect_size", "")).strip())
                        ),
                        adjusted_p_value=(
                            None
                            if not str(row.get("adjusted_p_value", "")).strip()
                            else float(str(row.get("adjusted_p_value", "")).strip())
                        ),
                        support_count=int(str(row.get("support_count", "")).strip()),
                        robustness_score=float(
                            str(row.get("robustness_score", "")).strip()
                        ),
                        assay_feasibility_score=float(
                            str(row.get("assay_feasibility_score", "")).strip()
                        ),
                        rank_reason_codes=_split_semicolon_field(
                            row.get("rank_reason_codes", "")
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biomarker-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = ("_load_validation_planning_biomarker_candidates",)
