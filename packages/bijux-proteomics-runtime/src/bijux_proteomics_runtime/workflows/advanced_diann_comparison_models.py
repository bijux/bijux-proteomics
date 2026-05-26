# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed comparison records for advanced DIA-NN runtime outputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class AdvancedDiannProteinComparisonState(StrEnum):
    """Stable comparison state for one advanced DIA-NN protein decision."""

    ABSENT = "absent"
    ACCEPTED = "accepted"
    DOWNGRADED = "downgraded"


class AdvancedDiannClaimComparisonState(StrEnum):
    """Stable comparison state for one advanced DIA-NN biological claim."""

    ABSENT = "absent"
    SUPPORTED = "supported"
    REJECTED = "rejected"


class AdvancedDiannRejectedRowComparisonState(StrEnum):
    """Stable comparison state for one q-value-filtered DIA-NN precursor row."""

    RETAINED = "retained"
    REJECTED = "rejected"


class AdvancedDiannParameterChangeEntry(JsonModel):
    """One scientific parameter difference between two advanced DIA-NN runs."""

    model_config = ConfigDict(extra="forbid")

    parameter_name: str = Field(..., min_length=1)
    left_value: str | float | bool | None = None
    right_value: str | float | bool | None = None
    note: str = Field(..., min_length=1)


class AdvancedDiannProteinChangeEntry(JsonModel):
    """One changed protein-level advanced DIA-NN outcome."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    representative_protein_ref: str | None = None
    left_state: AdvancedDiannProteinComparisonState
    right_state: AdvancedDiannProteinComparisonState
    note: str = Field(..., min_length=1)


class AdvancedDiannClaimChangeEntry(JsonModel):
    """One changed biological claim outcome between advanced DIA-NN runs."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    left_state: AdvancedDiannClaimComparisonState
    right_state: AdvancedDiannClaimComparisonState
    note: str = Field(..., min_length=1)


class AdvancedDiannRejectedRowChangeEntry(JsonModel):
    """One changed q-value-filtered precursor row between advanced DIA-NN runs."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    protein_group_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    run_name: str = Field(..., min_length=1)
    left_state: AdvancedDiannRejectedRowComparisonState
    right_state: AdvancedDiannRejectedRowComparisonState
    left_q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    right_q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class AdvancedDiannRuntimeComparisonReport(JsonModel):
    """Scientific comparison over two advanced DIA-NN runtime outputs."""

    model_config = ConfigDict(extra="forbid")

    left_workflow_id: str = Field(..., min_length=1)
    right_workflow_id: str = Field(..., min_length=1)
    equivalent: bool
    parameter_changes: tuple[AdvancedDiannParameterChangeEntry, ...] = Field(
        default_factory=tuple
    )
    changed_proteins: tuple[AdvancedDiannProteinChangeEntry, ...] = Field(
        default_factory=tuple
    )
    changed_claims: tuple[AdvancedDiannClaimChangeEntry, ...] = Field(
        default_factory=tuple
    )
    changed_rejected_rows: tuple[AdvancedDiannRejectedRowChangeEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


__all__ = [
    "AdvancedDiannClaimChangeEntry",
    "AdvancedDiannClaimComparisonState",
    "AdvancedDiannParameterChangeEntry",
    "AdvancedDiannProteinChangeEntry",
    "AdvancedDiannProteinComparisonState",
    "AdvancedDiannRejectedRowChangeEntry",
    "AdvancedDiannRejectedRowComparisonState",
    "AdvancedDiannRuntimeComparisonReport",
]
