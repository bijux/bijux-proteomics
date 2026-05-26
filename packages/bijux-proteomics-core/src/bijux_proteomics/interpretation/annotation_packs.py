# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed multi-table annotation pack loading for interpretation workflows."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import TypeVar

from pydantic import ConfigDict, Field, ValidationError, model_validator

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.complex_enrichment import (
    ComplexMemberKind,
    ComplexMembershipRecord,
)
from bijux_proteomics.interpretation.ortholog_mapping import OrthologRecord
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationRecord,
)
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceRecord,
    RegulatorEvidenceType,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import DocumentSchema, JsonModel

RowModel = TypeVar("RowModel", bound=JsonModel)


class AnnotationPackTableName(StrEnum):
    """Supported durable table names inside one annotation pack."""

    PROTEIN_FEATURES = "protein_features"
    PATHWAYS = "pathways"
    COMPLEXES = "complexes"
    COMPARTMENTS = "compartments"
    DRUG_TARGETS = "drug_targets"
    DISEASE_TERMS = "disease_terms"
    KINASE_SUBSTRATES = "kinase_substrates"
    ORTHOLOGS = "orthologs"


class AnnotationPackRejectedRow(JsonModel):
    """One rejected annotation-pack row with a stable table and reason."""

    model_config = ConfigDict(extra="forbid")

    table_name: AnnotationPackTableName
    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class AnnotationPackValidationReport(JsonModel):
    """Structured validation report for one annotation pack load."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    rejected_rows: tuple[AnnotationPackRejectedRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class AnnotationPackValidationError(ValueError):
    """Raised when an annotation pack contains invalid row-level schema."""

    def __init__(self, report: AnnotationPackValidationReport) -> None:
        self.report = report
        first_rejection = report.rejected_rows[0] if report.rejected_rows else None
        message = (
            "annotation pack validation failed"
            if first_rejection is None
            else (
                "annotation pack validation failed: "
                f"{first_rejection.table_name.value} row {first_rejection.row_number} "
                f"{first_rejection.reason}"
            )
        )
        super().__init__(message)


class AnnotationPackSummary(JsonModel):
    """Stable counts over one loaded annotation pack."""

    model_config = ConfigDict(extra="forbid")

    protein_feature_count: int = Field(..., ge=0)
    pathway_count: int = Field(..., ge=0)
    complex_count: int = Field(..., ge=0)
    compartment_count: int = Field(..., ge=0)
    drug_target_count: int = Field(..., ge=0)
    disease_term_count: int = Field(..., ge=0)
    kinase_substrate_count: int = Field(..., ge=0)
    ortholog_count: int = Field(..., ge=0)


class AnnotationPack(JsonModel):
    """One normalized annotation pack ready for downstream interpretation."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    pack_name: str = Field(..., min_length=1)
    pack_version: str | None = None
    document_schema: DocumentSchema | None = None
    protein_features: tuple[ProteinAnnotationRecord, ...] = Field(default_factory=tuple)
    pathways: tuple[PathwayMembershipRecord, ...] = Field(default_factory=tuple)
    complexes: tuple[ComplexMembershipRecord, ...] = Field(default_factory=tuple)
    compartments: tuple[BiologicalContextRecord, ...] = Field(default_factory=tuple)
    drug_targets: tuple[BiologicalContextRecord, ...] = Field(default_factory=tuple)
    disease_terms: tuple[BiologicalContextRecord, ...] = Field(default_factory=tuple)
    kinase_substrates: tuple[RegulatorEvidenceRecord, ...] = Field(default_factory=tuple)
    orthologs: tuple[OrthologRecord, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)
    summary: AnnotationPackSummary


class _ProteinFeaturePackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    description: str | None = None
    organism: str | None = None
    annotation_identifier: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_annotation_fields(self) -> _ProteinFeaturePackRow:
        if (
            self.gene_symbol is None
            and self.description is None
            and self.organism is None
            and self.annotation_identifier is None
        ):
            raise ValueError(
                "protein feature row requires at least one annotation field"
            )
        return self


class _PathwayPackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str | None = None
    gene_symbol: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_one_member(self) -> _PathwayPackRow:
        if self.protein_ref and self.gene_symbol:
            raise ValueError(
                "pathway row must choose protein_ref or gene_symbol, not both"
            )
        if self.protein_ref is None and self.gene_symbol is None:
            raise ValueError("pathway row requires protein_ref or gene_symbol")
        return self


class _ComplexPackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1)
    complex_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str | None = None
    gene_symbol: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_one_member(self) -> _ComplexPackRow:
        if self.protein_ref and self.gene_symbol:
            raise ValueError(
                "complex row must choose protein_ref or gene_symbol, not both"
            )
        if self.protein_ref is None and self.gene_symbol is None:
            raise ValueError("complex row requires protein_ref or gene_symbol")
        return self


class _BiologicalContextPackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    evidence: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class _KinaseSubstratePackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    regulator: str = Field(..., min_length=1)
    site_key: str = Field(..., min_length=1)
    source_name: str | None = None
    source_accession: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class _OrthologPackRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    source_species: str = Field(..., min_length=1)
    source_protein_ref: str = Field(..., min_length=1)
    target_species: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    source_gene_symbol: str | None = None
    target_gene_symbol: str | None = None
    evidence: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class _RawAnnotationPack(JsonModel):
    """Raw JSON envelope for one pack before row normalization."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema | None = None
    pack_name: str | None = None
    pack_version: str | None = None
    protein_features: list[object] = Field(default_factory=list)
    pathways: list[object] = Field(default_factory=list)
    complexes: list[object] = Field(default_factory=list)
    compartments: list[object] = Field(default_factory=list)
    drug_targets: list[object] = Field(default_factory=list)
    disease_terms: list[object] = Field(default_factory=list)
    kinase_substrates: list[object] = Field(default_factory=list)
    orthologs: list[object] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


def render_annotation_pack_json(pack: AnnotationPack) -> str:
    """Render one normalized annotation pack into canonical pack JSON."""

    payload: dict[str, object] = {
        "pack_name": pack.pack_name,
        "pack_version": pack.pack_version,
        "protein_features": [
            _serialize_protein_feature_row(record)
            for record in pack.protein_features
        ],
        "pathways": [_serialize_pathway_row(record) for record in pack.pathways],
        "complexes": [_serialize_complex_row(record) for record in pack.complexes],
        "compartments": [
            _serialize_biological_context_row(record)
            for record in pack.compartments
        ],
        "drug_targets": [
            _serialize_biological_context_row(record)
            for record in pack.drug_targets
        ],
        "disease_terms": [
            _serialize_biological_context_row(record)
            for record in pack.disease_terms
        ],
        "kinase_substrates": [
            _serialize_kinase_substrate_row(record)
            for record in pack.kinase_substrates
        ],
        "orthologs": [_serialize_ortholog_row(record) for record in pack.orthologs],
        "metadata": dict(pack.metadata),
    }
    if pack.document_schema is not None:
        payload["document_schema"] = pack.document_schema.to_dict()
    return json.dumps(payload, sort_keys=True) + "\n"


def load_annotation_pack(path: Path) -> AnnotationPack:
    """Load one governed JSON annotation pack with row-level validation."""

    raw_document = _RawAnnotationPack.model_validate_json(path.read_text(encoding="utf-8"))
    rejected_rows: list[AnnotationPackRejectedRow] = []

    protein_features = _load_protein_features(
        raw_document.protein_features,
        rejected_rows=rejected_rows,
    )
    pathways = _load_pathways(raw_document.pathways, rejected_rows=rejected_rows)
    complexes = _load_complexes(raw_document.complexes, rejected_rows=rejected_rows)
    compartments = _load_biological_context_table(
        raw_document.compartments,
        table_name=AnnotationPackTableName.COMPARTMENTS,
        context_kind=BiologicalContextKind.SUBCELLULAR_COMPARTMENT,
        rejected_rows=rejected_rows,
    )
    drug_targets = _load_biological_context_table(
        raw_document.drug_targets,
        table_name=AnnotationPackTableName.DRUG_TARGETS,
        context_kind=BiologicalContextKind.DRUG_TARGET,
        rejected_rows=rejected_rows,
    )
    disease_terms = _load_biological_context_table(
        raw_document.disease_terms,
        table_name=AnnotationPackTableName.DISEASE_TERMS,
        context_kind=BiologicalContextKind.DISEASE_TERM,
        rejected_rows=rejected_rows,
    )
    kinase_substrates = _load_kinase_substrates(
        raw_document.kinase_substrates,
        rejected_rows=rejected_rows,
    )
    orthologs = _load_orthologs(raw_document.orthologs, rejected_rows=rejected_rows)

    if rejected_rows:
        raise AnnotationPackValidationError(
            AnnotationPackValidationReport(
                source_path=str(path),
                rejected_rows=tuple(rejected_rows),
                note=(
                    "annotation pack loading rejected one or more rows before "
                    "downstream interpretation could consume unsupported schema"
                ),
            )
        )

    return AnnotationPack(
        source_path=str(path),
        pack_name=raw_document.pack_name or path.stem,
        pack_version=raw_document.pack_version,
        document_schema=raw_document.document_schema,
        protein_features=protein_features,
        pathways=pathways,
        complexes=complexes,
        compartments=compartments,
        drug_targets=drug_targets,
        disease_terms=disease_terms,
        kinase_substrates=kinase_substrates,
        orthologs=orthologs,
        metadata=raw_document.metadata,
        summary=AnnotationPackSummary(
            protein_feature_count=len(protein_features),
            pathway_count=len(pathways),
            complex_count=len(complexes),
            compartment_count=len(compartments),
            drug_target_count=len(drug_targets),
            disease_term_count=len(disease_terms),
            kinase_substrate_count=len(kinase_substrates),
            ortholog_count=len(orthologs),
        ),
    )


def _serialize_protein_feature_row(
    record: ProteinAnnotationRecord,
) -> dict[str, object]:
    return {
        "protein_ref": record.protein_ref,
        "gene_symbol": record.gene_symbol,
        "description": record.description,
        "organism": record.organism,
        "annotation_identifier": record.annotation_identifier,
        "metadata": dict(record.metadata),
    }


def _serialize_pathway_row(record: PathwayMembershipRecord) -> dict[str, object]:
    payload: dict[str, object] = {
        "pathway_id": record.pathway_id,
        "pathway_name": record.pathway_name,
        "source_name": record.source_name,
        "source_accession": record.source_accession,
        "protein_ref": None,
        "gene_symbol": None,
        "metadata": dict(record.metadata),
    }
    if record.member_kind is PathwayMemberKind.PROTEIN:
        payload["protein_ref"] = record.member_id
    else:
        payload["gene_symbol"] = record.member_id
    return payload


def _serialize_complex_row(record: ComplexMembershipRecord) -> dict[str, object]:
    payload: dict[str, object] = {
        "complex_id": record.complex_id,
        "complex_name": record.complex_name,
        "source_name": record.source_name,
        "source_accession": record.source_accession,
        "protein_ref": None,
        "gene_symbol": None,
        "metadata": dict(record.metadata),
    }
    if record.member_kind is ComplexMemberKind.PROTEIN:
        payload["protein_ref"] = record.member_id
    else:
        payload["gene_symbol"] = record.member_id
    return payload


def _serialize_biological_context_row(
    record: BiologicalContextRecord,
) -> dict[str, object]:
    return {
        "protein_ref": record.protein_ref,
        "context_id": record.context_id,
        "context_name": record.context_name,
        "source_name": record.source_name,
        "source_accession": record.source_accession,
        "evidence": record.evidence,
        "metadata": dict(record.metadata),
    }


def _serialize_kinase_substrate_row(
    record: RegulatorEvidenceRecord,
) -> dict[str, object]:
    return {
        "regulator": record.regulator,
        "site_key": record.site_key,
        "source_name": record.source_name,
        "source_accession": record.source_accession,
        "metadata": dict(record.metadata),
    }


def _serialize_ortholog_row(record: OrthologRecord) -> dict[str, object]:
    return {
        "source_species": record.source_species,
        "source_protein_ref": record.source_protein_ref,
        "target_species": record.target_species,
        "target_protein_ref": record.target_protein_ref,
        "source_gene_symbol": record.source_gene_symbol,
        "target_gene_symbol": record.target_gene_symbol,
        "evidence": record.evidence,
        "metadata": dict(record.metadata),
    }


def _load_protein_features(
    raw_rows: list[object],
    *,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[ProteinAnnotationRecord, ...]:
    accepted: list[ProteinAnnotationRecord] = []
    seen_protein_refs: set[str] = set()
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=AnnotationPackTableName.PROTEIN_FEATURES,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_ProteinFeaturePackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        protein_ref = canonicalize_protein_reference(row.protein_ref)
        if protein_ref in seen_protein_refs:
            rejected_rows.append(
                AnnotationPackRejectedRow(
                    table_name=AnnotationPackTableName.PROTEIN_FEATURES,
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=f"duplicate protein feature annotation for {protein_ref}",
                )
            )
            continue
        seen_protein_refs.add(protein_ref)
        accepted.append(
            ProteinAnnotationRecord(
                protein_ref=protein_ref,
                gene_symbol=row.gene_symbol,
                description=row.description,
                organism=row.organism,
                annotation_identifier=row.annotation_identifier,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _load_pathways(
    raw_rows: list[object],
    *,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[PathwayMembershipRecord, ...]:
    accepted: list[PathwayMembershipRecord] = []
    seen_memberships: set[tuple[str, str, str]] = set()
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=AnnotationPackTableName.PATHWAYS,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_PathwayPackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        if row.protein_ref is not None:
            member_kind = PathwayMemberKind.PROTEIN
            member_id = canonicalize_protein_reference(row.protein_ref)
        else:
            member_kind = PathwayMemberKind.GENE
            member_id = str(row.gene_symbol)
        membership_key = (row.pathway_id, member_kind.value, member_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                AnnotationPackRejectedRow(
                    table_name=AnnotationPackTableName.PATHWAYS,
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=(
                        f"duplicate pathway membership for {row.pathway_id} and {member_id}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted.append(
            PathwayMembershipRecord(
                pathway_id=row.pathway_id,
                pathway_name=row.pathway_name,
                source_name=row.source_name,
                source_accession=row.source_accession,
                member_kind=member_kind,
                member_id=member_id,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _load_complexes(
    raw_rows: list[object],
    *,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[ComplexMembershipRecord, ...]:
    accepted: list[ComplexMembershipRecord] = []
    seen_memberships: set[tuple[str, str, str]] = set()
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=AnnotationPackTableName.COMPLEXES,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_ComplexPackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        if row.protein_ref is not None:
            member_kind = ComplexMemberKind.PROTEIN
            member_id = canonicalize_protein_reference(row.protein_ref)
        else:
            member_kind = ComplexMemberKind.GENE
            member_id = str(row.gene_symbol)
        membership_key = (row.complex_id, member_kind.value, member_id)
        if membership_key in seen_memberships:
            rejected_rows.append(
                AnnotationPackRejectedRow(
                    table_name=AnnotationPackTableName.COMPLEXES,
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=(
                        f"duplicate complex membership for {row.complex_id} and {member_id}"
                    ),
                )
            )
            continue
        seen_memberships.add(membership_key)
        accepted.append(
            ComplexMembershipRecord(
                complex_id=row.complex_id,
                complex_name=row.complex_name,
                source_name=row.source_name,
                source_accession=row.source_accession,
                member_kind=member_kind,
                member_id=member_id,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _load_biological_context_table(
    raw_rows: list[object],
    *,
    table_name: AnnotationPackTableName,
    context_kind: BiologicalContextKind,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[BiologicalContextRecord, ...]:
    accepted: list[BiologicalContextRecord] = []
    seen_records: set[tuple[str, str, str, str | None, str | None]] = set()
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=table_name,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_BiologicalContextPackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        protein_ref = canonicalize_protein_reference(row.protein_ref)
        record_key = (
            protein_ref,
            context_kind.value,
            row.context_id,
            row.source_name,
            row.source_accession,
        )
        if record_key in seen_records:
            rejected_rows.append(
                AnnotationPackRejectedRow(
                    table_name=table_name,
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=(
                        f"duplicate {context_kind.value} annotation for "
                        f"{protein_ref} and {row.context_id}"
                    ),
                )
            )
            continue
        seen_records.add(record_key)
        accepted.append(
            BiologicalContextRecord(
                protein_ref=protein_ref,
                context_kind=context_kind,
                context_id=row.context_id,
                context_name=row.context_name,
                source_name=row.source_name,
                source_accession=row.source_accession,
                evidence=row.evidence,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _load_kinase_substrates(
    raw_rows: list[object],
    *,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[RegulatorEvidenceRecord, ...]:
    accepted: list[RegulatorEvidenceRecord] = []
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=AnnotationPackTableName.KINASE_SUBSTRATES,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_KinaseSubstratePackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        accepted.append(
            RegulatorEvidenceRecord(
                regulator=row.regulator,
                evidence_type=RegulatorEvidenceType.KINASE_SUBSTRATE,
                protein_ref=None,
                gene_symbol=None,
                pathway_id=None,
                site_key=row.site_key,
                source_name=row.source_name,
                source_accession=row.source_accession,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _load_orthologs(
    raw_rows: list[object],
    *,
    rejected_rows: list[AnnotationPackRejectedRow],
) -> tuple[OrthologRecord, ...]:
    accepted: list[OrthologRecord] = []
    seen_relationships: set[tuple[str, str, str, str]] = set()
    for row_number, raw_row in enumerate(raw_rows, start=1):
        row = _validate_row(
            table_name=AnnotationPackTableName.ORTHOLOGS,
            row_number=row_number,
            raw_row=raw_row,
            row_model=_OrthologPackRow,
            rejected_rows=rejected_rows,
        )
        if row is None:
            continue
        source_protein_ref = canonicalize_protein_reference(row.source_protein_ref)
        target_protein_ref = canonicalize_protein_reference(row.target_protein_ref)
        relationship_key = (
            row.source_species,
            source_protein_ref,
            row.target_species,
            target_protein_ref,
        )
        if relationship_key in seen_relationships:
            rejected_rows.append(
                AnnotationPackRejectedRow(
                    table_name=AnnotationPackTableName.ORTHOLOGS,
                    row_number=row_number,
                    values=_stringify_mapping(raw_row),
                    reason=(
                        "duplicate ortholog relationship for "
                        f"{row.source_species}:{source_protein_ref} -> "
                        f"{row.target_species}:{target_protein_ref}"
                    ),
                )
            )
            continue
        seen_relationships.add(relationship_key)
        accepted.append(
            OrthologRecord(
                source_species=row.source_species,
                source_protein_ref=source_protein_ref,
                target_species=row.target_species,
                target_protein_ref=target_protein_ref,
                source_gene_symbol=row.source_gene_symbol,
                target_gene_symbol=row.target_gene_symbol,
                evidence=row.evidence,
                metadata=row.metadata,
            )
        )
    return tuple(accepted)


def _validate_row(
    *,
    table_name: AnnotationPackTableName,
    row_number: int,
    raw_row: object,
    row_model: type[RowModel],
    rejected_rows: list[AnnotationPackRejectedRow],
) -> RowModel | None:
    if not isinstance(raw_row, dict):
        rejected_rows.append(
            AnnotationPackRejectedRow(
                table_name=table_name,
                row_number=row_number,
                values={"_raw_row": _stringify_scalar(raw_row)},
                reason="annotation pack rows must be JSON objects",
            )
        )
        return None
    try:
        return row_model.model_validate(raw_row, strict=True)
    except ValidationError as exc:
        rejected_rows.append(
            AnnotationPackRejectedRow(
                table_name=table_name,
                row_number=row_number,
                values=_stringify_mapping(raw_row),
                reason=_stable_validation_reason(exc),
            )
        )
        return None
    except ValueError as exc:
        rejected_rows.append(
            AnnotationPackRejectedRow(
                table_name=table_name,
                row_number=row_number,
                values=_stringify_mapping(raw_row),
                reason=str(exc),
            )
        )
        return None


def _stringify_mapping(raw_row: object) -> dict[str, str]:
    if not isinstance(raw_row, dict):
        return {"_raw_row": _stringify_scalar(raw_row)}
    return {
        str(key): _stringify_scalar(value)
        for key, value in raw_row.items()
    }


def _stringify_scalar(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return str(value)


def _stable_validation_reason(error: ValidationError) -> str:
    reasons: list[str] = []
    for issue in error.errors():
        location = ".".join(str(token) for token in issue.get("loc", ()))
        message = str(issue.get("msg", "invalid field"))
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        if location:
            reasons.append(f"{location}: {message}")
        else:
            reasons.append(message)
    return "; ".join(reasons)


__all__ = [
    "AnnotationPack",
    "AnnotationPackRejectedRow",
    "AnnotationPackSummary",
    "AnnotationPackTableName",
    "AnnotationPackValidationError",
    "AnnotationPackValidationReport",
    "load_annotation_pack",
    "render_annotation_pack_json",
]
