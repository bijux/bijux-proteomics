# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

import pytest

from bijux_proteomics.chemistry import (
    IsotopicLabelingPolicy,
    build_modified_peptide,
    build_peptide_elemental_composition,
    modification_registry,
    predict_peptide_isotope_envelope,
)

_C13_NEUTRON_SHIFT = 1.0033548378


def test_isotope_envelope_prediction_preserves_formula_probability_and_spacing() -> (
    None
):
    composition = build_peptide_elemental_composition("PEPTIDE")
    envelope = predict_peptide_isotope_envelope("PEPTIDE", charge=2)

    assert composition.formula == "C34H53N7O15"
    assert composition.carbon == 34
    assert composition.hydrogen == 53
    assert composition.nitrogen == 7
    assert composition.oxygen == 15
    assert len(envelope.peaks) == 6
    assert isclose(
        sum(peak.probability for peak in envelope.peaks),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-6,
    )
    assert isclose(
        envelope.peaks[1].mz - envelope.peaks[0].mz,
        _C13_NEUTRON_SHIFT / 2.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def test_modified_peptide_isotope_envelope_applies_registry_elemental_deltas() -> None:
    peptide = build_modified_peptide(
        "PESTIDE",
        assignments=("Phospho@3", "Acetyl@n-term"),
        registry=modification_registry(),
    )

    composition = build_peptide_elemental_composition(
        peptide,
        registry=modification_registry(),
    )
    envelope = predict_peptide_isotope_envelope(
        peptide,
        charge=3,
        registry=modification_registry(),
    )

    assert composition.formula == "C34H54N7O20P1"
    assert composition.phosphorus == 1
    assert envelope.peaks[0].mz == envelope.monoisotopic_mz
    assert envelope.max_isotope_index == 5


def test_isotope_envelope_prediction_rejects_explicit_isotope_labels() -> None:
    peptide = build_modified_peptide(
        "AK",
        assignments=("HeavyLys8@2",),
        registry=modification_registry(),
        labeling_policy=IsotopicLabelingPolicy(
            allow_isotopic_labels=True,
            allowed_label_families=("silac_lys",),
        ),
    )

    with pytest.raises(
        ValueError,
        match="does not support explicit isotope-label modification",
    ):
        predict_peptide_isotope_envelope(
            peptide,
            charge=2,
            registry=modification_registry(),
        )
