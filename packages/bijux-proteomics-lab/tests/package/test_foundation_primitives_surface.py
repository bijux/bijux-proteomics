# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pydantic import ValidationError
import pytest

from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_lab.planning import ExperimentPlan


def test_lab_plans_use_foundation_document_and_identifier_primitives() -> None:
    plan = ExperimentPlan(program_id="prog-lab")

    assert issubclass(ExperimentPlan, JsonModel)
    assert isinstance(plan.document_schema, DocumentSchema)

    with pytest.raises(ValidationError):
        ExperimentPlan(program_id="Program Lab")
