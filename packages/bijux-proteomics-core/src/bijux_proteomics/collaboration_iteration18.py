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


class MethodsSectionInput(JsonModel):
    """Structured workflow evidence used to render methods text."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    workflow_steps: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    software_versions: tuple[str, ...] = Field(default_factory=tuple)


class MethodsSectionDocument(JsonModel):
    """Generated methods section fragment with explicit evidence references."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


def generate_methods_section_from_workflow_evidence(
    payload: MethodsSectionInput,
) -> MethodsSectionDocument:
    """Generate methods narrative from exact workflow and evidence references."""

    steps = "; ".join(payload.workflow_steps) if payload.workflow_steps else "workflow steps unspecified"
    versions = ", ".join(payload.software_versions) if payload.software_versions else "software versions unavailable"
    refs = ", ".join(payload.evidence_refs) if payload.evidence_refs else "no evidence references"
    body = (
        f"{payload.title}: executed pipeline steps [{steps}] using software versions [{versions}]. "
        f"Evidence linkage references: [{refs}]."
    )
    return MethodsSectionDocument(title=payload.title, body=body)


class CitationRegistryEntry(JsonModel):
    """Citation attachment for tool/algorithm/reference/method evidence usage."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(..., min_length=1)
    citation_kind: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)


class CitationRegistryDocument(JsonModel):
    """Registry of citations linked to workflow evidence outputs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CitationRegistryEntry, ...] = Field(default_factory=tuple)


def build_citation_registry_document(
    entries: tuple[CitationRegistryEntry, ...],
) -> CitationRegistryDocument:
    """Attach tool/algorithm/reference/method citations to evidence pointers."""

    normalized = tuple(sorted(entries, key=lambda entry: (entry.citation_kind, entry.citation_id)))
    return CitationRegistryDocument(entries=normalized)


class StandaloneVerifierInput(JsonModel):
    """Standalone verifier input that does not depend on repository checkout paths."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    hash_ledger_entries: tuple[str, ...] = Field(default_factory=tuple)


class StandaloneVerifierIssue(JsonModel):
    """Verifier issue found during standalone bundle validation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class StandaloneVerifierReport(JsonModel):
    """Standalone verification report for external bundles."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    verified: bool
    issues: tuple[StandaloneVerifierIssue, ...] = Field(default_factory=tuple)


def run_standalone_bundle_verifier(
    payload: StandaloneVerifierInput,
) -> StandaloneVerifierReport:
    """Verify bundle structure without requiring repository checkout context."""

    issues: list[StandaloneVerifierIssue] = []
    if not payload.schema_refs:
        issues.append(
            StandaloneVerifierIssue(
                code="missing_schema_refs",
                message="bundle must include at least one schema reference",
            )
        )
    if not payload.hash_ledger_entries:
        issues.append(
            StandaloneVerifierIssue(
                code="missing_hash_ledger",
                message="bundle must include hash ledger entries",
            )
        )
    for path in payload.artifact_paths:
        if path.startswith("/"):
            issues.append(
                StandaloneVerifierIssue(
                    code="absolute_artifact_path",
                    message="artifact paths must be portable relative paths",
                )
            )
            break

    return StandaloneVerifierReport(
        bundle_id=payload.bundle_id,
        verified=not issues,
        issues=tuple(issues),
    )


class ArchiveRetentionPackageInput(JsonModel):
    """Input for long-term archive packaging."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    compatibility_metadata: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class ArchiveRetentionPackage(JsonModel):
    """Archive package containing long-term preservation metadata and references."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    compatibility_metadata: tuple[str, ...] = Field(default_factory=tuple)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


def build_archive_retention_package(
    payload: ArchiveRetentionPackageInput,
) -> ArchiveRetentionPackage:
    """Build archive package with compatibility metadata and caveat traceability."""

    return ArchiveRetentionPackage(
        package_id=payload.package_id,
        schema_refs=tuple(sorted(set(payload.schema_refs))),
        artifact_paths=tuple(sorted(set(payload.artifact_paths))),
        evidence_pointer_ids=tuple(sorted(set(payload.evidence_pointer_ids))),
        compatibility_metadata=tuple(sorted(set(payload.compatibility_metadata))),
        caveats=tuple(sorted(set(payload.caveats))),
    )
