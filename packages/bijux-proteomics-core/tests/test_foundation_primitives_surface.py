# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pydantic import ValidationError
import pytest

from bijux_proteomics.domain.program_spec import ProgramSpec, create_program_spec
from bijux_proteomics_foundation import DocumentSchema, JsonModel


def test_core_program_models_use_foundation_document_and_identifier_primitives() -> None:
    program = create_program_spec(
        program_id="prog-core",
        name="Core program",
        objective="Validate foundation ownership",
        target_id="target-core",
        target_name="MAPK1",
        sequence="MPEPTIDE",
        organism="human",
        mechanism="kinase modulation",
    )

    assert issubclass(ProgramSpec, JsonModel)
    assert isinstance(program.document_schema, DocumentSchema)

    with pytest.raises(ValidationError):
        create_program_spec(
            program_id="Program Core",
            name="Core program",
            objective="Validate foundation ownership",
            target_id="target-core",
            target_name="MAPK1",
            sequence="MPEPTIDE",
            organism="human",
            mechanism="kinase modulation",
        )
