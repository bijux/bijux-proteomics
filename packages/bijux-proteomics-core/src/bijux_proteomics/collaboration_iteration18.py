# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Collaboration, review, and security surfaces for iteration 18."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ExternalReviewerBundleInput(JsonModel):
    """Input payload for building an external reviewer bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    summary_lines: tuple[str, ...] = Field(default_factory=tuple)
    hash_ledger_entries: tuple[str, ...] = Field(default_factory=tuple)
    reviewer_instructions: str = Field(..., min_length=1)


class ExternalReviewerBundle(JsonModel):
    """Export bundle for external review with schema/evidence/hash/instruction context."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    summary_lines: tuple[str, ...] = Field(default_factory=tuple)
    hash_ledger_entries: tuple[str, ...] = Field(default_factory=tuple)
    reviewer_instructions: str = Field(..., min_length=1)
    completeness_notes: tuple[str, ...] = Field(default_factory=tuple)


def build_external_reviewer_bundle(
    payload: ExternalReviewerBundleInput,
) -> ExternalReviewerBundle:
    """Build external reviewer bundle with explicit completeness notes."""

    notes: list[str] = []
    if not payload.schema_refs:
        notes.append("missing schema references")
    if not payload.evidence_pointer_ids:
        notes.append("missing evidence pointers")
    if not payload.hash_ledger_entries:
        notes.append("missing hash ledger entries")

    return ExternalReviewerBundle(
        bundle_id=payload.bundle_id,
        schema_refs=tuple(sorted(set(payload.schema_refs))),
        evidence_pointer_ids=tuple(sorted(set(payload.evidence_pointer_ids))),
        summary_lines=tuple(payload.summary_lines),
        hash_ledger_entries=tuple(sorted(set(payload.hash_ledger_entries))),
        reviewer_instructions=payload.reviewer_instructions,
        completeness_notes=tuple(notes),
    )


class RedactedCollaborationBundleInput(JsonModel):
    """Raw collaboration bundle input that may contain sensitive path/sample text."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    file_paths: tuple[str, ...] = Field(default_factory=tuple)
    provenance_links: tuple[str, ...] = Field(default_factory=tuple)


class RedactedCollaborationBundle(JsonModel):
    """Redacted collaboration bundle preserving reviewable provenance references."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    redacted_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    redacted_file_paths: tuple[str, ...] = Field(default_factory=tuple)
    provenance_links: tuple[str, ...] = Field(default_factory=tuple)


def build_redacted_collaboration_bundle(
    payload: RedactedCollaborationBundleInput,
) -> RedactedCollaborationBundle:
    """Redact sensitive sample/path fields while preserving provenance link structure."""

    redacted_samples = tuple(f"SAMPLE_{index + 1:03d}" for index, _ in enumerate(payload.sample_ids))
    redacted_paths = tuple(f"<redacted-path-{index + 1:03d}>" for index, _ in enumerate(payload.file_paths))
    return RedactedCollaborationBundle(
        bundle_id=payload.bundle_id,
        redacted_sample_ids=redacted_samples,
        redacted_file_paths=redacted_paths,
        provenance_links=tuple(payload.provenance_links),
    )
