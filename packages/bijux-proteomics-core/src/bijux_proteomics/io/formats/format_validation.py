# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared validation contracts for proteomics format ingestion."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class FormatValidationIssue(JsonModel):
    """One stable format-validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    field: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    record_id: str | None = None
