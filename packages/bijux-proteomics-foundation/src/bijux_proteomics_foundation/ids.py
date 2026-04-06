# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Typed identifiers shared across Bijux Proteomics packages."""

from __future__ import annotations

from typing import Annotated

from pydantic import StringConstraints

Identifier = StringConstraints(
    strip_whitespace=True,
    min_length=1,
    max_length=128,
    pattern=r"^[a-z0-9][a-z0-9._:-]*$",
)

ProgramId = Annotated[str, Identifier]
TargetId = Annotated[str, Identifier]
CandidateId = Annotated[str, Identifier]
AssayId = Annotated[str, Identifier]
EvidenceId = Annotated[str, Identifier]
BatchId = Annotated[str, Identifier]
GateId = Annotated[str, Identifier]
CycleId = Annotated[str, Identifier]
