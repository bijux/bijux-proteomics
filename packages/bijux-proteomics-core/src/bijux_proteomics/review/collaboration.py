# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""External collaboration, redaction, and verification surfaces."""

from __future__ import annotations

from hashlib import sha256
import re

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

    redacted_samples = tuple(
        f"SAMPLE_{index + 1:03d}" for index, _ in enumerate(payload.sample_ids)
    )
    redacted_paths = tuple(
        f"<redacted-path-{index + 1:03d}>" for index, _ in enumerate(payload.file_paths)
    )
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

    steps = (
        "; ".join(payload.workflow_steps)
        if payload.workflow_steps
        else "workflow steps unspecified"
    )
    versions = (
        ", ".join(payload.software_versions)
        if payload.software_versions
        else "software versions unavailable"
    )
    refs = (
        ", ".join(payload.evidence_refs)
        if payload.evidence_refs
        else "no evidence references"
    )
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

    normalized = tuple(
        sorted(entries, key=lambda entry: (entry.citation_kind, entry.citation_id))
    )
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


class CollaboratorChallengeInput(JsonModel):
    """External collaborator challenge attached to evidence claims."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    evidence_claim_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    comment: str = Field(..., min_length=1)


class CollaboratorChallengeEntry(JsonModel):
    """Stored collaborator challenge with linkability to evidence claims."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    evidence_claim_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)


class CollaboratorChallengeWorkflowReport(JsonModel):
    """Workflow report for collaborator challenges on evidence claims."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CollaboratorChallengeEntry, ...] = Field(default_factory=tuple)


def run_collaborator_challenge_workflow(
    items: tuple[CollaboratorChallengeInput, ...],
) -> CollaboratorChallengeWorkflowReport:
    """Attach external collaborator comments/questions to evidence claims."""

    entries = tuple(
        CollaboratorChallengeEntry(
            challenge_id=item.challenge_id,
            reviewer_id=item.reviewer_id,
            evidence_claim_id=item.evidence_claim_id,
            prompt=f"Q: {item.question} | Comment: {item.comment}",
            status="open",
        )
        for item in items
    )
    return CollaboratorChallengeWorkflowReport(entries=entries)


class SignedReviewerBundleInput(JsonModel):
    """Input payload for signing reviewer bundles."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    manifest_entries: tuple[str, ...] = Field(default_factory=tuple)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    review_packet_ids: tuple[str, ...] = Field(default_factory=tuple)
    hash_ledger_entries: tuple[str, ...] = Field(default_factory=tuple)
    signing_key_id: str = Field(..., min_length=1)
    signing_secret: str = Field(..., min_length=8)


class SignedReviewerBundle(JsonModel):
    """Signed reviewer bundle with canonicalized references and signature metadata."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    manifest_entries: tuple[str, ...] = Field(default_factory=tuple)
    schema_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointer_ids: tuple[str, ...] = Field(default_factory=tuple)
    review_packet_ids: tuple[str, ...] = Field(default_factory=tuple)
    hash_ledger_entries: tuple[str, ...] = Field(default_factory=tuple)
    signing_key_id: str = Field(..., min_length=1)
    signature_algorithm: str = Field(..., min_length=1)
    signature_hex: str = Field(..., min_length=1)


def _canonical_signed_bundle_message(payload: SignedReviewerBundleInput) -> str:
    manifest = tuple(sorted(set(payload.manifest_entries)))
    schemas = tuple(sorted(set(payload.schema_refs)))
    evidence = tuple(sorted(set(payload.evidence_pointer_ids)))
    packets = tuple(sorted(set(payload.review_packet_ids)))
    ledger = tuple(sorted(set(payload.hash_ledger_entries)))
    sections = (
        payload.bundle_id.strip(),
        "|".join(manifest),
        "|".join(schemas),
        "|".join(evidence),
        "|".join(packets),
        "|".join(ledger),
    )
    return "||".join(sections)


def build_signed_reviewer_bundle(
    payload: SignedReviewerBundleInput,
) -> SignedReviewerBundle:
    """Sign canonical reviewer bundle content and emit deterministic signature metadata."""

    message = _canonical_signed_bundle_message(payload)
    signature_hex = sha256(f"{payload.signing_secret}::{message}".encode()).hexdigest()
    return SignedReviewerBundle(
        bundle_id=payload.bundle_id,
        manifest_entries=tuple(sorted(set(payload.manifest_entries))),
        schema_refs=tuple(sorted(set(payload.schema_refs))),
        evidence_pointer_ids=tuple(sorted(set(payload.evidence_pointer_ids))),
        review_packet_ids=tuple(sorted(set(payload.review_packet_ids))),
        hash_ledger_entries=tuple(sorted(set(payload.hash_ledger_entries))),
        signing_key_id=payload.signing_key_id,
        signature_algorithm="sha256-secret-v1",
        signature_hex=signature_hex,
    )


def verify_signed_reviewer_bundle(
    bundle: SignedReviewerBundle,
    signing_secret: str,
) -> bool:
    """Verify signed reviewer bundle integrity using the canonical signing message."""

    rebuilt_payload = SignedReviewerBundleInput(
        bundle_id=bundle.bundle_id,
        manifest_entries=bundle.manifest_entries,
        schema_refs=bundle.schema_refs,
        evidence_pointer_ids=bundle.evidence_pointer_ids,
        review_packet_ids=bundle.review_packet_ids,
        hash_ledger_entries=bundle.hash_ledger_entries,
        signing_key_id=bundle.signing_key_id,
        signing_secret=signing_secret,
    )
    expected = build_signed_reviewer_bundle(rebuilt_payload)
    return expected.signature_hex == bundle.signature_hex


_PATH_PATTERN = re.compile(r"(?<!\w)(?:[A-Za-z]:\\[^\s]+|/[^\s]+)")
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*([^\s,;]+)"),
    re.compile(r"(?i)\b(bearer)\s+([a-z0-9._\-]+)"),
)


class CollaborationSurfaceRedactionInput(JsonModel):
    """Potentially sensitive collaboration text surfaces for redaction checks."""

    model_config = ConfigDict(extra="forbid")

    log_lines: tuple[str, ...] = Field(default_factory=tuple)
    api_errors: tuple[str, ...] = Field(default_factory=tuple)
    evidence_notes: tuple[str, ...] = Field(default_factory=tuple)
    review_packet_notes: tuple[str, ...] = Field(default_factory=tuple)


class CollaborationSurfaceRedactionReport(JsonModel):
    """Redacted collaboration surfaces while preserving diagnostic sentence structure."""

    model_config = ConfigDict(extra="forbid")

    log_lines: tuple[str, ...] = Field(default_factory=tuple)
    api_errors: tuple[str, ...] = Field(default_factory=tuple)
    evidence_notes: tuple[str, ...] = Field(default_factory=tuple)
    review_packet_notes: tuple[str, ...] = Field(default_factory=tuple)
    redaction_count: int = Field(..., ge=0)


def _redact_text(value: str) -> tuple[str, int]:
    updated = value
    redactions = 0
    for pattern in _SECRET_PATTERNS:
        updated, hits = pattern.subn(
            lambda match: f"{match.group(1)}=<redacted-secret>", updated
        )
        redactions += hits
    updated, path_hits = _PATH_PATTERN.subn("<redacted-path>", updated)
    redactions += path_hits
    return updated, redactions


def _redact_collection(values: tuple[str, ...]) -> tuple[tuple[str, ...], int]:
    redacted: list[str] = []
    total_hits = 0
    for entry in values:
        updated, hits = _redact_text(entry)
        redacted.append(updated)
        total_hits += hits
    return tuple(redacted), total_hits


def redact_collaboration_surfaces(
    payload: CollaborationSurfaceRedactionInput,
) -> CollaborationSurfaceRedactionReport:
    """Redact secrets and path disclosures across collaboration-facing text surfaces."""

    redacted_logs, log_hits = _redact_collection(payload.log_lines)
    redacted_errors, error_hits = _redact_collection(payload.api_errors)
    redacted_evidence, evidence_hits = _redact_collection(payload.evidence_notes)
    redacted_packets, packet_hits = _redact_collection(payload.review_packet_notes)
    return CollaborationSurfaceRedactionReport(
        log_lines=redacted_logs,
        api_errors=redacted_errors,
        evidence_notes=redacted_evidence,
        review_packet_notes=redacted_packets,
        redaction_count=log_hits + error_hits + evidence_hits + packet_hits,
    )


class HostileInputProtectionInput(JsonModel):
    """Untrusted archive and table metadata entering collaboration pipelines."""

    model_config = ConfigDict(extra="forbid")

    archive_members: tuple[str, ...] = Field(default_factory=tuple)
    record_sizes_bytes: tuple[int, ...] = Field(default_factory=tuple)
    xml_payloads: tuple[str, ...] = Field(default_factory=tuple)
    table_rows: tuple[str, ...] = Field(default_factory=tuple)
    max_record_size_bytes: int = Field(default=5_000_000, ge=1)


class HostileInputProtectionIssue(JsonModel):
    """Refusal reason for unsafe external input."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class HostileInputProtectionReport(JsonModel):
    """Validation outcome for hostile input protection checks."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool
    issues: tuple[HostileInputProtectionIssue, ...] = Field(default_factory=tuple)


_HOSTILE_FILENAME_PATTERN = re.compile(r"[`$|;&<>]")


def run_hostile_input_protection(
    payload: HostileInputProtectionInput,
) -> HostileInputProtectionReport:
    """Refuse malformed archives, unsafe paths, oversized records, and corrupt content."""

    issues: list[HostileInputProtectionIssue] = []

    for member in payload.archive_members:
        if not member or "\x00" in member:
            issues.append(
                HostileInputProtectionIssue(
                    code="malformed_archive_member",
                    message="archive member name is empty or contains NUL byte",
                )
            )
            continue
        if member.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", member):
            issues.append(
                HostileInputProtectionIssue(
                    code="absolute_archive_path",
                    message="archive member must be a relative path",
                )
            )
        parts = re.split(r"[\\/]+", member)
        if ".." in parts:
            issues.append(
                HostileInputProtectionIssue(
                    code="path_traversal",
                    message="archive member includes parent path traversal",
                )
            )
        if _HOSTILE_FILENAME_PATTERN.search(member):
            issues.append(
                HostileInputProtectionIssue(
                    code="hostile_filename",
                    message="archive member contains unsafe shell metacharacters",
                )
            )

    for size in payload.record_sizes_bytes:
        if size > payload.max_record_size_bytes:
            issues.append(
                HostileInputProtectionIssue(
                    code="oversized_record",
                    message="record exceeds maximum safe byte size",
                )
            )
            break

    for xml in payload.xml_payloads:
        normalized = xml.upper()
        if "<!DOCTYPE" in normalized or "<!ENTITY" in normalized:
            issues.append(
                HostileInputProtectionIssue(
                    code="xml_entity_abuse",
                    message="xml payload contains forbidden doctype/entity declarations",
                )
            )
            break

    if payload.table_rows:
        expected_columns = len(payload.table_rows[0].split("\t"))
        for row in payload.table_rows:
            if "\x00" in row:
                issues.append(
                    HostileInputProtectionIssue(
                        code="corrupt_table",
                        message="table row contains NUL byte",
                    )
                )
                break
            if len(row.split("\t")) != expected_columns:
                issues.append(
                    HostileInputProtectionIssue(
                        code="corrupt_table",
                        message="table rows contain inconsistent column counts",
                    )
                )
                break

    return HostileInputProtectionReport(accepted=not issues, issues=tuple(issues))
