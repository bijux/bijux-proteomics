# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain import (
    DesignError,
    InvalidWorkflowError,
    SchemaError,
    ScientificEvidenceError,
    UnsupportedFormatError,
)
from bijux_proteomics.domain.errors import BijuxProteomicsError


def test_domain_error_surface_exposes_workflow_facing_exception_families() -> None:
    for error_type in (
        SchemaError,
        DesignError,
        ScientificEvidenceError,
        UnsupportedFormatError,
        InvalidWorkflowError,
    ):
        assert issubclass(error_type, BijuxProteomicsError)

    assert str(SchemaError("invalid schema")) == "invalid schema"
    assert str(DesignError("invalid design")) == "invalid design"
    assert str(ScientificEvidenceError("missing evidence")) == "missing evidence"
    assert str(UnsupportedFormatError("unsupported format")) == "unsupported format"
    assert str(InvalidWorkflowError("invalid workflow")) == "invalid workflow"
