# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared schema metadata for Bijux Proteomics documents."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import hashlib
import json

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
    document_id: str | None = Field(
        default=None,
        description="Stable identifier for the durable document artifact.",
    )
    document_kind: str | None = Field(
        default=None,
        description="Document kind such as program_spec or evidence_bundle.",
    )
    package_name: str | None = Field(
        default=None,
        description="Package that produced the document payload.",
    )
    package_version: str | None = Field(
        default=None,
        description="Package version that produced the payload.",
    )
    status: str = Field(
        default="draft",
        min_length=1,
        description="Lifecycle status such as draft, reviewed, or superseded.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream document identifiers this artifact derives from.",
    )
    parent_document_id: str | None = Field(
        default=None,
        description="Immediate parent document identifier when superseded or revised.",
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
    revision: int = Field(
        default=1,
        ge=1,
        description="Monotonic revision number for the document.",
    )
    content_hash: str | None = Field(
        default=None,
        description="Optional stable hash for document content.",
    )

    def touch(self, actor: str, *, tag: str | None = None) -> DocumentSchema:
        """Return a copy with updated audit metadata."""
        tags = list(self.tags)
        if tag is not None and tag not in tags:
            tags.append(tag)
        return self.model_copy(
            update={
                "updated_at": datetime.now(UTC),
                "updated_by": actor,
                "tags": tags,
                "revision": self.revision + 1,
            }
        )

    def with_content_hash(self, payload: dict[str, object]) -> DocumentSchema:
        """Return a copy with deterministic content hash from a payload."""
        stable = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()
        return self.model_copy(update={"content_hash": digest})


class SchemaCompatibility(StrEnum):
    """Compatibility status for expected versus observed schema versions."""

    COMPATIBLE = "compatible"
    FORWARD_INCOMPATIBLE = "forward_incompatible"
    BACKWARD_INCOMPATIBLE = "backward_incompatible"


def assess_schema_compatibility(
    observed: str,
    expected: str,
) -> SchemaCompatibility:
    """Assess compatibility using major/minor version semantics."""
    observed_major, observed_minor, *_ = [int(part) for part in observed.split(".")]
    expected_major, expected_minor, *_ = [int(part) for part in expected.split(".")]
    if observed_major != expected_major:
        return SchemaCompatibility.BACKWARD_INCOMPATIBLE
    if observed_minor < expected_minor:
        return SchemaCompatibility.FORWARD_INCOMPATIBLE
    return SchemaCompatibility.COMPATIBLE
