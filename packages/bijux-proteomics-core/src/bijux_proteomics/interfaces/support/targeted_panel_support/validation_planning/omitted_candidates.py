# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Omitted-candidate TSV loading for validation planning entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.validation_planning import (
    ValidationPlanningOmittedCandidateInput,
)


def _load_validation_planning_omitted_candidates(
    path: Path,
) -> tuple[ValidationPlanningOmittedCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel omitted-candidate TSV must include a header row for validation planning"
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
                "panel omitted-candidate TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningOmittedCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningOmittedCandidateInput(
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


__all__ = ("_load_validation_planning_omitted_candidates",)
