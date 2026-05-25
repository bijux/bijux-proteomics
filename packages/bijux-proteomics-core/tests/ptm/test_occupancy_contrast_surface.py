# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.ptm import (
    PtmOccupancyConfidenceTier,
    render_ptm_occupancy_contrast_tsv,
    test_occupancy_contrast,
)
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)


def test_occupancy_contrast_estimates_case_control_change_and_downgrades_missing_unmodified() -> None:
    modified = _occupancy_matrix(
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
            "Q9DEC1:S5:Phospho": {
                "ctrl-1": None,
                "ctrl-2": None,
                "case-1": 5.0,
                "case-2": 6.0,
            },
        }
    )
    unmodified = _occupancy_matrix(
        {
            "P11111:S5:Phospho": {
                "ctrl-1": 90.0,
                "ctrl-2": 88.0,
                "case-1": 20.0,
                "case-2": 16.0,
            },
            "Q9DEC1:S5:Phospho": {
                "ctrl-1": 95.0,
                "ctrl-2": 96.0,
                "case-1": 70.0,
                "case-2": 74.0,
            },
        }
    )

    report = test_occupancy_contrast(modified, unmodified, _design())
    rendered = render_ptm_occupancy_contrast_tsv(report)
    by_site = {entry.site_id: entry for entry in report.entries}

    assert report.condition_control == "control"
    assert report.condition_case == "case"
    high_confidence = by_site["P11111:S5:Phospho"]
    missing_unmodified = by_site["P22222:Y18:Phospho"]
    missing_modified = by_site["Q9DEC1:S5:Phospho"]

    assert high_confidence.occupancy_proxy_control == 0.11
    assert high_confidence.occupancy_proxy_case == 0.82
    assert high_confidence.occupancy_delta == 0.71
    assert high_confidence.confidence_tier is PtmOccupancyConfidenceTier.HIGH_CONFIDENCE
    assert high_confidence.p_value < 0.1
    assert missing_unmodified.occupancy_proxy_control == 1.0
    assert missing_unmodified.occupancy_proxy_case == 1.0
    assert (
        missing_unmodified.confidence_tier
        is PtmOccupancyConfidenceTier.MISSING_UNMODIFIED_EVIDENCE
    )
    assert missing_modified.occupancy_proxy_control == 0.0
    assert missing_modified.occupancy_proxy_case == 0.070833
    assert (
        missing_modified.confidence_tier
        is PtmOccupancyConfidenceTier.MISSING_MODIFIED_EVIDENCE
    )
    assert rendered.startswith(
        "site_id\toccupancy_proxy_case\toccupancy_proxy_control\toccupancy_delta\tp_value\tq_value\tconfidence_tier\n"
    )


def test_occupancy_contrast_requires_exactly_two_conditions() -> None:
    matrix = _occupancy_matrix(
        {
            "P11111:S5:Phospho": {
                "s1": 10.0,
                "s2": 12.0,
                "s3": 15.0,
            },
        }
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="s1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s2.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="s3.raw",
        ),
    )

    with pytest.raises(ValueError, match="exactly two conditions"):
        test_occupancy_contrast(matrix, matrix, design)


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


def _design() -> tuple[ExperimentalDesignEntry, ...]:
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
