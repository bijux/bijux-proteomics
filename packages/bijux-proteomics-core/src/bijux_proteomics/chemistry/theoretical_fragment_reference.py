# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Theoretical fragment reference validation for modified peptide fixtures."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts.fragment_ions import (
    calculate_fragment_ions,
)
from bijux_proteomics.chemistry.contracts.models import (
    FragmentIonSeries,
)
from bijux_proteomics.chemistry.contracts.modified_peptides import (
    parse_modified_peptide,
)
from bijux_proteomics.chemistry.modification_registry import (
    modification_registry,
)
from bijux_proteomics.chemistry.public_api import rebind_package_export
from bijux_proteomics_foundation import JsonModel

rebind_package_export(
    "bijux_proteomics.chemistry",
    "modification_registry",
    modification_registry,
)


class TheoreticalFragmentReferenceIon(JsonModel):
    """One expected ion in a theoretical fragmentation reference case."""

    model_config = ConfigDict(extra="forbid")

    series: FragmentIonSeries
    ordinal: int = Field(..., ge=1)
    charge: int = Field(..., ge=1)
    neutral_loss: str | None = None
    expected_mz_monoisotopic: float = Field(..., gt=0.0)
    tolerance_da: float = Field(default=0.02, gt=0.0)


class TheoreticalFragmentReferenceCase(JsonModel):
    """One peptide-level fragmentation reference fixture."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    expected_ions: tuple[TheoreticalFragmentReferenceIon, ...] = Field(
        default_factory=tuple
    )


class TheoreticalFragmentValidationEntry(JsonModel):
    """Validation row for one expected ion in a fixture case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    series: FragmentIonSeries
    ordinal: int = Field(..., ge=1)
    charge: int = Field(..., ge=1)
    neutral_loss: str | None = None
    expected_mz_monoisotopic: float = Field(..., gt=0.0)
    observed_mz_monoisotopic: float | None = None
    delta_da: float | None = None
    passed: bool


class TheoreticalFragmentValidationReport(JsonModel):
    """Validation report over a reference fixture set."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    case_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    failed_entry_count: int = Field(..., ge=0)
    entries: tuple[TheoreticalFragmentValidationEntry, ...] = Field(
        default_factory=tuple
    )


def validate_theoretical_fragment_reference_cases(
    cases: Sequence[TheoreticalFragmentReferenceCase],
) -> TheoreticalFragmentValidationReport:
    """Validate theoretical fragmentation fixtures against the ion engine."""
    registry = modification_registry()
    entries: list[TheoreticalFragmentValidationEntry] = []
    for case in cases:
        peptide = parse_modified_peptide(case.modified_peptide, registry=registry)
        observed_ions = calculate_fragment_ions(
            peptide,
            charges=tuple(sorted({ion.charge for ion in case.expected_ions})),
            series=tuple(sorted({ion.series for ion in case.expected_ions}, key=str)),
            include_neutral_losses=True,
            registry=registry,
        )
        for expected in case.expected_ions:
            match = next(
                (
                    ion
                    for ion in observed_ions
                    if ion.series is expected.series
                    and ion.ordinal == expected.ordinal
                    and ion.charge == expected.charge
                    and ion.neutral_loss == expected.neutral_loss
                ),
                None,
            )
            observed = match.mz_monoisotopic if match is not None else None
            delta = (
                observed - expected.expected_mz_monoisotopic
                if observed is not None
                else None
            )
            passed = observed is not None and abs(delta or 0.0) <= expected.tolerance_da
            entries.append(
                TheoreticalFragmentValidationEntry(
                    case_id=case.case_id,
                    series=expected.series,
                    ordinal=expected.ordinal,
                    charge=expected.charge,
                    neutral_loss=expected.neutral_loss,
                    expected_mz_monoisotopic=expected.expected_mz_monoisotopic,
                    observed_mz_monoisotopic=observed,
                    delta_da=delta,
                    passed=passed,
                )
            )
    failed = sum(1 for entry in entries if not entry.passed)
    return TheoreticalFragmentValidationReport(
        valid=failed == 0,
        case_count=len(cases),
        entry_count=len(entries),
        failed_entry_count=failed,
        entries=tuple(entries),
    )
