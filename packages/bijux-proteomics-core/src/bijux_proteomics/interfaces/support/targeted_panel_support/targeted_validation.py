# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted validation and redundancy TSV loaders for interface entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.panel_redundancy import PanelRedundancyCandidateInput
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationDiscoveryClaimInput,
)

from ..targeted_selection_io.field_parsing import _split_semicolon_field


def _load_targeted_validation_discovery_claims(
    path: Path,
) -> tuple[TargetedValidationDiscoveryClaimInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for targeted result validation"
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
            "effect_size",
            "support_count",
            "robustness_score",
            "assay_feasibility_score",
            "rank_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for targeted result validation: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedValidationDiscoveryClaimInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    TargetedValidationDiscoveryClaimInput(
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
                        discovery_effect_size=(
                            None
                            if not str(row.get("effect_size", "")).strip()
                            else float(str(row.get("effect_size", "")).strip())
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


def _load_panel_redundancy_candidates(
    path: Path,
) -> tuple[PanelRedundancyCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for panel redundancy analysis"
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
            "rank_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for panel redundancy analysis: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[PanelRedundancyCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    PanelRedundancyCandidateInput(
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


__all__ = [
    "_load_panel_redundancy_candidates",
    "_load_targeted_validation_discovery_claims",
]
