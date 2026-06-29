# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Targeted panel biomarker candidate input loaders."""

from __future__ import annotations

from ..imports import *  # noqa: F401,F403
from ..targeted_selection_io.field_parsing import _split_semicolon_field


def _load_biomarker_candidate_inputs(
    path: Path,
) -> tuple[TargetedPanelBiomarkerCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for targeted panel building"
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
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelBiomarkerCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    TargetedPanelBiomarkerCandidateInput(
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
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biomarker-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)
