# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.interpretation import (
    BiologicalSetFilteringPolicy,
    BiologicalSetSourceKind,
    InvalidBackgroundAction,
    ProteinReferenceEntry,
    build_biological_foreground_background_model,
    render_biological_foreground_background_issue_tsv,
    require_valid_biological_foreground_background_model,
)


def _entry(protein_ref: str, row_id: str) -> ProteinReferenceEntry:
    return ProteinReferenceEntry(
        row_number=2,
        source_row_id=row_id,
        input_protein_ref=protein_ref,
        protein_ref=protein_ref,
    )


def test_foreground_background_model_warns_when_background_comes_from_annotation_universe() -> (
    None
):
    model = build_biological_foreground_background_model(
        (_entry("P11111", "foreground:1"),),
        (
            _entry("P11111", "background:1"),
            _entry("P22222", "background:2"),
        ),
        foreground_source_kind=BiologicalSetSourceKind.DIFFERENTIAL_SIGNIFICANT_RESULTS,
        background_source_kind=BiologicalSetSourceKind.ANNOTATION_UNIVERSE,
        foreground_policy=BiologicalSetFilteringPolicy(
            policy_name="significant proteins",
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
            note="foreground keeps significant proteins from the contrast",
        ),
        background_policy=BiologicalSetFilteringPolicy(
            policy_name="annotation universe",
            measured_entities_only=False,
            note="background was taken from the annotation universe",
        ),
        invalid_background_action=InvalidBackgroundAction.WARN,
    )

    assert model.summary.valid_for_enrichment is True
    assert model.summary.issue_count == 1
    assert model.issues[0].code == "annotation_universe_background"
    assert (
        "annotation or membership universe"
        in render_biological_foreground_background_issue_tsv(model)
    )


def test_foreground_background_model_rejects_invalid_background_when_requested() -> (
    None
):
    model = build_biological_foreground_background_model(
        (_entry("P11111", "foreground:1"),),
        (_entry("P22222", "background:1"),),
        foreground_source_kind=BiologicalSetSourceKind.DIFFERENTIAL_SIGNIFICANT_RESULTS,
        background_source_kind=BiologicalSetSourceKind.EXPLICIT_INPUT,
        foreground_policy=BiologicalSetFilteringPolicy(
            policy_name="significant proteins",
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
            note="foreground keeps significant proteins from the contrast",
        ),
        background_policy=BiologicalSetFilteringPolicy(
            policy_name="explicit input",
            note="background came from an explicit table",
        ),
    )

    assert model.summary.valid_for_enrichment is False
    with pytest.raises(ValueError, match="foreground proteins must all be present"):
        require_valid_biological_foreground_background_model(model)
