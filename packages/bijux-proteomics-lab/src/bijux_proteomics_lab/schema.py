# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Schema metadata for lab planning documents."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_lab.serialization import JsonModel


class SchemaMetadata(JsonModel):
    """Cross-system metadata for planning documents."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Version of the document schema.",
    )
    created_by: str = Field(
        default="bijux-proteomics-lab",
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
