# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared schema metadata for Bijux Proteomics documents."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization import JsonModel


class DocumentSchema(JsonModel):
    """Cross-system metadata for long-lived platform documents."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Version of the document schema.",
    )
    created_by: str = Field(
        ...,
        min_length=1,
        description="Producer of the document.",
    )
    source_system: str = Field(
        default="bijux-proteomics",
        min_length=1,
        description="System where the document originated.",
    )
    trace_id: str | None = Field(
        default=None,
        description="Optional cross-system trace identifier.",
    )
