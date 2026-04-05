# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein sequence domain models."""

from __future__ import annotations

import re

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel, TargetId

_SEQUENCE_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")


class ProteinSequence(JsonModel):
    """Canonical protein sequence document."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Target identifier.")
    residues: str = Field(..., min_length=1, description="Canonical amino-acid sequence.")

    @field_validator("residues")
    @classmethod
    def _validate_residues(cls, value: str) -> str:
        sequence = value.strip().upper()
        if not _SEQUENCE_RE.fullmatch(sequence):
            raise ValueError("residues must contain only canonical amino-acid symbols")
        return sequence


def sequence_length(sequence: ProteinSequence) -> int:
    """Return the amino-acid length of a canonical sequence."""
    return len(sequence.residues)
