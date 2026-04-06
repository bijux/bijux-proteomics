# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Adapter contracts for external evidence ingestion."""

from __future__ import annotations

from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.evidence import (
    EvidenceBundle,
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)
from bijux_proteomics_knowledge.serialization import JsonModel, fingerprint_model


class NormalizedEvidenceInput(JsonModel):
    """Normalized evidence payload produced by an ingestion adapter."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(
        ..., min_length=1, description="Stable evidence identifier."
    )
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Evidence title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    source_type: EvidenceSourceType = Field(..., description="Source category.")
    claim: str = Field(..., min_length=1, description="Normalized claim text.")
    related_targets: list[str] = Field(
        default_factory=list,
        description="Targets referenced by the payload.",
    )
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the payload.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    strength: EvidenceStrength = Field(..., description="Support level.")
    source_uri: str | None = Field(
        default=None,
        description="Optional stable URI or note locator.",
    )
    curator: str | None = Field(
        default=None,
        description="Human or system that prepared the normalized payload.",
    )
    origin: EvidenceOrigin = Field(
        default=EvidenceOrigin.IMPORTED,
        description="Origin classification for the imported payload.",
    )
    extraction_method: EvidenceExtractionMethod = Field(
        default=EvidenceExtractionMethod.AUTOMATED_IMPORT,
        description="How the normalized payload was produced.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream evidence identifiers or note references.",
    )
    assay_modality: str | None = Field(
        default=None, description="Assay modality context."
    )
    biological_system: str | None = Field(
        default=None, description="Biological system context."
    )
    species: str | None = Field(default=None, description="Species context.")
    sample_type: str | None = Field(default=None, description="Sample or matrix type.")
    endpoint: str | None = Field(default=None, description="Primary measured endpoint.")
    dose: str | None = Field(
        default=None, description="Dose level or concentration context."
    )
    timepoint: str | None = Field(
        default=None, description="Measurement timepoint context."
    )
    perturbation: str | None = Field(
        default=None, description="Perturbation applied in the experiment."
    )
    control_design: str | None = Field(default=None, description="Control arm design.")
    replicate_design: str | None = Field(
        default=None, description="Replicate strategy used for the experiment."
    )
    normalization_method: str | None = Field(
        default=None, description="Normalization method for quantitative values."
    )
    sample_preparation: str | None = Field(
        default=None, description="Sample preparation protocol."
    )
    tissue_context: str | None = Field(
        default=None, description="Tissue context when relevant."
    )
    cell_line_context: str | None = Field(
        default=None, description="Cell line context when relevant."
    )
    quantitative_support: QuantitativeSupport | None = Field(
        default=None,
        description="Optional quantitative support for the claim.",
    )


class ManualEvidenceNote(JsonModel):
    """Curated note captured directly from a scientist or reviewer."""

    model_config = ConfigDict(extra="forbid")

    note_id: str = Field(..., min_length=1, description="Stable note identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    title: str = Field(..., min_length=1, description="Short note title.")
    claim: str = Field(..., min_length=1, description="Claim captured by the curator.")
    curator: str = Field(..., min_length=1, description="Person who captured the note.")
    kind: EvidenceKind = Field(
        ..., description="Evidence family represented by the note."
    )
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the note.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Curator confidence.")
    strength: EvidenceStrength = Field(..., description="Support level of the note.")
    source_uri: str | None = Field(
        default=None,
        description="Optional note locator in an external system.",
    )
    biological_system: str | None = Field(
        default=None,
        description="Biological system referenced by the note.",
    )
    species: str | None = Field(
        default=None,
        description="Species context referenced by the note.",
    )
    sample_type: str | None = Field(
        default=None, description="Sample context referenced by the note."
    )
    endpoint: str | None = Field(
        default=None, description="Primary endpoint referenced by the note."
    )
    dose: str | None = Field(
        default=None, description="Dose context referenced by the note."
    )
    timepoint: str | None = Field(
        default=None, description="Timepoint context referenced by the note."
    )


class LiteratureIngestionAdapter(Protocol):
    """Adapter contract for literature-derived evidence."""

    def ingest_literature(self, target_id: str) -> list[NormalizedEvidenceInput]:
        """Return normalized evidence payloads for a target."""


class AssayResultIngestionAdapter(Protocol):
    """Adapter contract for assay-derived evidence."""

    def ingest_assay_results(self, target_id: str) -> list[NormalizedEvidenceInput]:
        """Return normalized assay payloads for a target."""


class StructureAnnotationIngestionAdapter(Protocol):
    """Adapter contract for structure-derived evidence."""

    def ingest_structure_annotations(
        self,
        target_id: str,
    ) -> list[NormalizedEvidenceInput]:
        """Return normalized structural payloads for a target."""


class ManualEvidenceNoteAdapter(Protocol):
    """Adapter contract for curated manual notes."""

    def ingest_manual_notes(self, target_id: str) -> list[ManualEvidenceNote]:
        """Return curated notes for a target."""


class IngestionReport(JsonModel):
    """Summary of one ingestion run into an evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(
        ..., min_length=1, description="Target evidence bundle identifier."
    )
    added_records: int = Field(default=0, ge=0, description="Number of records added.")
    skipped_records: int = Field(
        default=0, ge=0, description="Number of records skipped."
    )
    duplicate_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers skipped because they already existed.",
    )
    rejected_records: int = Field(
        default=0, ge=0, description="Number of records rejected by validation."
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for rejected normalized inputs.",
    )
    accepted_fingerprints: dict[str, str] = Field(
        default_factory=dict,
        description="Stable fingerprints for accepted normalized evidence payloads.",
    )


def validate_normalized_input(
    item: NormalizedEvidenceInput,
    *,
    target_id: str,
) -> list[str]:
    """Return validation issues for a normalized evidence input."""
    issues: list[str] = []
    if (
        item.kind in {EvidenceKind.ASSAY, EvidenceKind.CELLULAR, EvidenceKind.PHENOTYPE}
        and not item.endpoint
    ):
        issues.append(
            f"{item.evidence_id}: endpoint is required for assay-like evidence"
        )
    if (
        item.quantitative_support is not None
        and item.quantitative_support.replicate_count is None
    ):
        issues.append(
            f"{item.evidence_id}: quantitative support should include replicate_count"
        )
    if item.related_targets and target_id not in item.related_targets:
        issues.append(
            f"{item.evidence_id}: related_targets does not include bundle target '{target_id}'"
        )
    return issues


def attach_evidence_inputs(
    bundle: EvidenceBundle,
    inputs: list[NormalizedEvidenceInput],
) -> EvidenceBundle:
    """Attach normalized adapter outputs to an existing bundle."""
    records = [
        *bundle.records,
        *[
            EvidenceRecord(
                evidence_id=item.evidence_id,
                kind=item.kind,
                title=item.title,
                source=item.source,
                source_type=item.source_type,
                source_uri=item.source_uri,
                origin=item.origin,
                extraction_method=item.extraction_method,
                curator=item.curator,
                claim=item.claim,
                related_targets=item.related_targets,
                decision_tags=item.decision_tags,
                derived_from=item.derived_from,
                assay_modality=item.assay_modality,
                biological_system=item.biological_system,
                species=item.species,
                sample_type=item.sample_type,
                endpoint=item.endpoint,
                dose=item.dose,
                timepoint=item.timepoint,
                perturbation=item.perturbation,
                control_design=item.control_design,
                replicate_design=item.replicate_design,
                normalization_method=item.normalization_method,
                sample_preparation=item.sample_preparation,
                tissue_context=item.tissue_context,
                cell_line_context=item.cell_line_context,
                quantitative_support=item.quantitative_support,
                confidence=item.confidence,
                strength=item.strength,
            )
            for item in inputs
        ],
    ]
    return bundle.model_copy(update={"records": records})


def attach_manual_notes(
    bundle: EvidenceBundle,
    notes: list[ManualEvidenceNote],
) -> EvidenceBundle:
    """Attach manually curated notes to an existing bundle."""
    return attach_evidence_inputs(
        bundle,
        [
            NormalizedEvidenceInput(
                evidence_id=note.note_id,
                kind=note.kind,
                title=note.title,
                source=f"manual-note:{note.curator}",
                source_type=EvidenceSourceType.CURATED_NOTE,
                source_uri=note.source_uri,
                claim=note.claim,
                related_targets=[note.target_id],
                decision_tags=note.decision_tags,
                confidence=note.confidence,
                strength=note.strength,
                curator=note.curator,
                origin=EvidenceOrigin.OBSERVED,
                extraction_method=EvidenceExtractionMethod.MANUAL_CURATION,
                biological_system=note.biological_system,
                species=note.species,
                sample_type=note.sample_type,
                endpoint=note.endpoint,
                dose=note.dose,
                timepoint=note.timepoint,
            )
            for note in notes
        ],
    )


def ingest_inputs_with_report(
    bundle: EvidenceBundle,
    inputs: list[NormalizedEvidenceInput],
) -> tuple[EvidenceBundle, IngestionReport]:
    """Attach normalized inputs and return an auditable ingestion report."""
    existing_ids = {record.evidence_id for record in bundle.records}
    accepted: list[NormalizedEvidenceInput] = []
    duplicate_ids: list[str] = []
    rejection_reasons: list[str] = []
    rejected_records = 0
    accepted_fingerprints: dict[str, str] = {}
    for item in inputs:
        if item.evidence_id in existing_ids:
            duplicate_ids.append(item.evidence_id)
            continue
        issues = validate_normalized_input(item, target_id=bundle.target_id)
        if issues:
            rejected_records += 1
            rejection_reasons.extend(issues)
            continue
        existing_ids.add(item.evidence_id)
        accepted.append(item)
        accepted_fingerprints[item.evidence_id] = fingerprint_model(item)
    updated = attach_evidence_inputs(bundle, accepted)
    report = IngestionReport(
        bundle_id=bundle.bundle_id,
        added_records=len(accepted),
        skipped_records=len(duplicate_ids),
        duplicate_ids=duplicate_ids,
        rejected_records=rejected_records,
        rejection_reasons=rejection_reasons,
        accepted_fingerprints=accepted_fingerprints,
    )
    return updated, report
