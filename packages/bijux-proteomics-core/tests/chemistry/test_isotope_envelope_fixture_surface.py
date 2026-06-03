# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from math import isclose
from pathlib import Path

from bijux_proteomics.chemistry import (
    build_modified_peptide,
    modification_registry,
    predict_peptide_isotope_envelope,
)


def _chemistry_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "chemistry" / name


def test_isotope_envelope_prediction_matches_curated_reference_cases() -> None:
    cases = json.loads(
        _chemistry_fixture("isotope_envelope_reference_cases.json").read_text()
    )

    for case in cases:
        peptide = build_modified_peptide(
            case["sequence"],
            assignments=tuple(case["assignments"]),
            registry=modification_registry(),
        )
        envelope = predict_peptide_isotope_envelope(
            peptide,
            charge=case["charge"],
            registry=modification_registry(),
        )

        assert envelope.composition.formula == case["expected_formula"], case["case_id"]
        assert isclose(
            envelope.monoisotopic_mz,
            case["expected_monoisotopic_mz"],
            rel_tol=0.0,
            abs_tol=1e-12,
        ), case["case_id"]
        assert len(envelope.peaks) == len(case["expected_probabilities"]), case[
            "case_id"
        ]
        for peak, expected_probability in zip(
            envelope.peaks,
            case["expected_probabilities"],
            strict=True,
        ):
            assert isclose(
                peak.probability,
                expected_probability,
                rel_tol=0.0,
                abs_tol=1e-12,
            ), case["case_id"]
