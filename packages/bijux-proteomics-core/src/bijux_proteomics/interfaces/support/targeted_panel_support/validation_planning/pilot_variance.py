# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pilot-variance TSV loading for validation planning entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.targeted.validation_planning import (
    ValidationPlanningPilotVarianceInput,
)

from ...targeted_selection_io.field_parsing import (
    _parse_cli_bool,
    _split_semicolon_field,
)


def _load_validation_planning_pilot_variance(
    path: Path,
) -> tuple[ValidationPlanningPilotVarianceInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "power-variance TSV must include a header row for validation planning"
            )
        required_columns = {
            "entity_id",
            "protein_refs",
            "observed_sample_count",
            "missing_fraction",
            "contributing_condition_count",
            "used_global_variance_fallback",
            "pooled_log2_stddev",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "power-variance TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningPilotVarianceInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningPilotVarianceInput(
                        entity_id=str(row.get("entity_id", "")).strip(),
                        protein_refs=tuple(
                            value
                            for value in _split_semicolon_field(
                                row.get("protein_refs", "")
                            )
                            if value
                        ),
                        observed_sample_count=int(
                            str(row.get("observed_sample_count", "")).strip()
                        ),
                        missing_fraction=float(
                            str(row.get("missing_fraction", "")).strip()
                        ),
                        contributing_condition_count=int(
                            str(row.get("contributing_condition_count", "")).strip()
                        ),
                        used_global_variance_fallback=_parse_cli_bool(
                            row.get("used_global_variance_fallback", ""),
                            field_name="used_global_variance_fallback",
                        ),
                        pooled_log2_stddev=float(
                            str(row.get("pooled_log2_stddev", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid power-variance row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = ("_load_validation_planning_pilot_variance",)
