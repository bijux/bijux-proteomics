# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared schema metadata for Bijux Proteomics documents."""

from __future__ import annotations

from datetime import UTC, datetime

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
    parent_trace_id: str | None = Field(
        default=None,
        description="Optional parent trace for lineage across document derivations.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Durable tags for indexing and filtering documents.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the document metadata was first created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the document metadata was last updated.",
    )
    updated_by: str | None = Field(
        default=None,
        description="Actor that most recently touched this document metadata.",
    )

    def touch(self, actor: str, *, tag: str | None = None) -> "DocumentSchema":
        """Return a copy with updated audit metadata."""
        tags = list(self.tags)
        if tag is not None and tag not in tags:
            tags.append(tag)
        return self.model_copy(
            update={
                "updated_at": datetime.now(UTC),
                "updated_by": actor,
                "tags": tags,
            }
        )
