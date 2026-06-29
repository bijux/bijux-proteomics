# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Validation evidence candidate quality loaders."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.biomarker_stability.models import (
    BiomarkerStabilityReasonCode,
)
from bijux_proteomics.targeted.validation_evidence_cards import (
    ValidationEvidenceRedundancyInput,
    ValidationEvidenceStabilityInput,
)

from ..targeted_selection_io.field_parsing import (
    _parse_cli_bool,
    _split_semicolon_field,
)


def _load_validation_evidence_stability_entries(
    path: Path,
) -> tuple[ValidationEvidenceStabilityInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "stability TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "stability_score",
            "stability_penalty",
            "downgraded",
            "instability_reasons",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "stability TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceStabilityInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceStabilityInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        stability_score=float(
                            str(row.get("stability_score", "")).strip()
                        ),
                        stability_penalty=float(
                            str(row.get("stability_penalty", "")).strip()
                        ),
                        downgraded=_parse_cli_bool(
                            row.get("downgraded", ""),
                            field_name="downgraded",
                        ),
                        instability_reasons=tuple(
                            BiomarkerStabilityReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("instability_reasons", "")
                            )
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid stability row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_validation_evidence_redundancy_entries(
    path: Path,
) -> tuple[ValidationEvidenceRedundancyInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "redundancy TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "cluster_id",
            "representative_candidate_id",
            "representative",
            "dropped",
            "shared_sample_count",
            "max_redundant_correlation",
            "redundancy_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "redundancy TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceRedundancyInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceRedundancyInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        cluster_id=str(row.get("cluster_id", "")).strip(),
                        representative_candidate_id=str(
                            row.get("representative_candidate_id", "")
                        ).strip(),
                        representative=_parse_cli_bool(
                            row.get("representative", ""),
                            field_name="representative",
                        ),
                        dropped=_parse_cli_bool(
                            row.get("dropped", ""),
                            field_name="dropped",
                        ),
                        shared_sample_count=int(
                            str(row.get("shared_sample_count", "")).strip()
                        ),
                        max_redundant_correlation=(
                            None
                            if not str(row.get("max_redundant_correlation", "")).strip()
                            else float(
                                str(row.get("max_redundant_correlation", "")).strip()
                            )
                        ),
                        redundancy_reason_codes=_split_semicolon_field(
                            row.get("redundancy_reason_codes", "")
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid redundancy row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = [
    "_load_validation_evidence_redundancy_entries",
    "_load_validation_evidence_stability_entries",
]
