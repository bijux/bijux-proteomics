# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from math import isclose
from pathlib import Path

from bijux_proteomics.chemistry import build_peptide_mass_report

_ABS_TOLERANCE_MASS = 1e-6
_ABS_TOLERANCE_MZ = 1e-9


def _chemistry_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "chemistry" / name


def test_curated_amino_acid_mass_examples_match_fixed_expected_values() -> None:
    fixture = json.loads(
        _chemistry_fixture("amino_acid_mass_examples.json").read_text()
    )

    for case in fixture:
        report = build_peptide_mass_report(
            case["sequence"],
            charge=case["charge"],
        )

        assert isclose(
            report.neutral_monoisotopic_mass,
            case["neutral_monoisotopic_mass"],
            rel_tol=0.0,
            abs_tol=_ABS_TOLERANCE_MASS,
        )
        assert isclose(
            report.neutral_average_mass,
            case["neutral_average_mass"],
            rel_tol=0.0,
            abs_tol=_ABS_TOLERANCE_MASS,
        )
        assert isclose(
            report.mz_monoisotopic,
            case["mz_monoisotopic"],
            rel_tol=0.0,
            abs_tol=_ABS_TOLERANCE_MZ,
        )
        assert isclose(
            report.mz_average,
            case["mz_average"],
            rel_tol=0.0,
            abs_tol=_ABS_TOLERANCE_MZ,
        )
