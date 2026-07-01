# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

import bijux_proteomics.interfaces as interface_examples
from bijux_proteomics.interfaces.examples import (
    build_glycopeptide_refusal_example,
    build_loss_aware_search_normalization_example,
    build_sequence_digest_example,
)


def test_sequence_digest_example_stays_runtime_free_and_scientific() -> None:
    example = build_sequence_digest_example()

    assert example.example_id == "core.sequence-digest"
    assert example.owner_surface == "bijux_proteomics.sequences.digestion"
    assert "MPEPTIDERK" in example.observations[1].value
    assert "runtime" in example.caveats[0]


def test_glycopeptide_refusal_example_names_missing_evidence() -> None:
    example = build_glycopeptide_refusal_example()

    assert example.example_id == "core.glycopeptide-refusal"
    assert example.observations[0].value == "refused"
    assert "glycan_composition" in example.observations[1].value
    assert "ordinary residue modifications" in example.caveats[0]


def test_loss_aware_search_normalization_example_reports_preserved_and_lost_fields() -> (
    None
):
    example = build_loss_aware_search_normalization_example()

    observations = {entry.label: entry.value for entry in example.observations}

    assert example.example_id == "core.loss-aware-search-normalization"
    assert observations["preserved_native_only_columns"] == "analysis_batch"
    assert observations["unsupported_columns"] == "novel_metric"
    assert observations["lost_columns"] == "missing_runtime_tag"


def test_interfaces_package_root_exports_curated_example_surface() -> None:
    assert interface_examples.__all__ == (
        "CoreScientificExample",
        "ScientificExampleObservation",
        "build_glycopeptide_refusal_example",
        "build_loss_aware_search_normalization_example",
        "build_sequence_digest_example",
    )
    assert (
        interface_examples.build_sequence_digest_example
        is build_sequence_digest_example
    )
    assert (
        interface_examples.build_glycopeptide_refusal_example
        is build_glycopeptide_refusal_example
    )
    assert (
        interface_examples.build_loss_aware_search_normalization_example
        is build_loss_aware_search_normalization_example
    )


def test_interfaces_package_root_rejects_unknown_exports() -> None:
    with pytest.raises(AttributeError):
        object.__getattribute__(interface_examples, "missing_example")
