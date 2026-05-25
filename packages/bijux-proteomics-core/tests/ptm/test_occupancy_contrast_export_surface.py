# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import render_ptm_occupancy_contrast_tsv, test_occupancy_contrast
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)


def test_render_ptm_occupancy_contrast_tsv_preserves_delta_and_confidence() -> None:
    report = test_occupancy_contrast(
        _occupancy_matrix(
            {
                "P11111:S5:Phospho": {
                    "ctrl-1": 10.0,
                    "ctrl-2": 12.0,
                    "case-1": 80.0,
                    "case-2": 84.0,
                },
                "P22222:Y18:Phospho": {
                    "ctrl-1": 20.0,
                    "ctrl-2": 25.0,
                    "case-1": 35.0,
                    "case-2": 40.0,
                },
            }
        ),
        _occupancy_matrix(
            {
                "P11111:S5:Phospho": {
                    "ctrl-1": 90.0,
                    "ctrl-2": 88.0,
                    "case-1": 20.0,
                    "case-2": 16.0,
                },
            }
        ),
        _occupancy_design(),
    )
    rendered = render_ptm_occupancy_contrast_tsv(report)

    assert rendered.startswith(
        "site_id\toccupancy_proxy_case\toccupancy_proxy_control\toccupancy_delta\tp_value\tq_value\tconfidence_tier\n"
    )
    assert (
        "\nP11111:S5:Phospho\t0.82\t0.11\t0.71\t" in rendered
    )
    assert rendered.rstrip().endswith("missing_unmodified_evidence")


def _occupancy_matrix(
    site_values: dict[str, dict[str, float | None]],
) -> LabelFreeQuantTable:
    sample_ids = tuple(
        sorted({sample_id for values in site_values.values() for sample_id in values})
    )
    entity_ids = tuple(sorted(site_values))
    values: list[QuantValue] = []
    for entity_id in entity_ids:
        row = site_values[entity_id]
        for sample_id in sample_ids:
            abundance = row.get(sample_id)
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=(
                        MissingValueKind.OBSERVED
                        if abundance is not None
                        else MissingValueKind.NOT_OBSERVED
                    ),
                    source_feature_count=0 if abundance is None else 1,
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        sample_ids=sample_ids,
        entity_ids=entity_ids,
        values=tuple(values),
    )


def _occupancy_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.raw",
        ),
    )
