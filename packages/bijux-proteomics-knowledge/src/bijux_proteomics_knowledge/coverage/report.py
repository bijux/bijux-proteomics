# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Aggregate knowledge coverage over result entity sets."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import Callable, TypeVar

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.annotation_packs import (
    AnnotationPack,
    AnnotationPackSummary,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.identity.proteins import (
    ProteinIdentityResolutionStatus,
    resolve_protein_ids,
)
from bijux_proteomics_knowledge.kinases.substrates import resolve_kinase_substrates

RecordT = TypeVar("RecordT")


class KnowledgeCoverageEntityType(StrEnum):
    """Supported result-entity families for aggregate knowledge coverage."""

    PROTEIN = "protein"
    PATHWAY = "pathway"
    PTM_SITE = "ptm_site"
    REGULATOR = "regulator"


class KnowledgeCoverageEntitySet(JsonModel):
    """One result-entity family to measure against available knowledge packs."""

    model_config = ConfigDict(extra="forbid")

    entity_type: KnowledgeCoverageEntityType
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)


class KnowledgeCoveragePolicy(JsonModel):
    """Coverage thresholds that trigger interpretation downgrade warnings."""

    model_config = ConfigDict(extra="forbid")

    protein_min_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    pathway_min_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    ptm_site_min_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    regulator_min_coverage_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


class KnowledgeCoverageEntry(JsonModel):
    """One aggregate knowledge-coverage row for one result-entity family."""

    model_config = ConfigDict(extra="forbid")

    entity_type: KnowledgeCoverageEntityType
    total_count: int = Field(..., ge=0)
    annotated_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    low_coverage_warning: str | None = None


class KnowledgeCoverageSummary(JsonModel):
    """Stable summary over one knowledge coverage evaluation."""

    model_config = ConfigDict(extra="forbid")

    entity_type_count: int = Field(..., ge=0)
    low_coverage_entity_type_count: int = Field(..., ge=0)


class KnowledgeCoverageReport(JsonModel):
    """Owned report over result-entity annotation coverage."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[KnowledgeCoverageEntry, ...] = Field(default_factory=tuple)
    summary: KnowledgeCoverageSummary
    note: str = Field(..., min_length=1)


def compute_knowledge_coverage(
    result_entities: tuple[KnowledgeCoverageEntitySet, ...],
    packs: AnnotationPack | tuple[AnnotationPack, ...],
    *,
    policy: KnowledgeCoveragePolicy | None = None,
) -> KnowledgeCoverageReport:
    """Compute aggregate annotation coverage across result-entity families."""

    active_policy = policy or KnowledgeCoveragePolicy()
    normalized_packs = _normalize_packs(packs)
    merged_pack = _merge_annotation_packs(normalized_packs)
    pathway_ids = {record.pathway_id for record in merged_pack.pathways}
    regulator_ids = {record.regulator.strip().casefold() for record in merged_pack.kinase_substrates}

    entries: list[KnowledgeCoverageEntry] = []
    for entity_set in result_entities:
        total_count = len(entity_set.entity_ids)
        annotated_count = _annotated_count(
            entity_set=entity_set,
            merged_pack=merged_pack,
            pathway_ids=pathway_ids,
            regulator_ids=regulator_ids,
        )
        coverage_fraction = (
            annotated_count / total_count if total_count > 0 else 0.0
        )
        entries.append(
            KnowledgeCoverageEntry(
                entity_type=entity_set.entity_type,
                total_count=total_count,
                annotated_count=annotated_count,
                coverage_fraction=round(coverage_fraction, 4),
                low_coverage_warning=_low_coverage_warning(
                    entity_type=entity_set.entity_type,
                    coverage_fraction=coverage_fraction,
                    policy=active_policy,
                ),
            )
        )

    sorted_entries = tuple(sorted(entries, key=lambda entry: entry.entity_type.value))
    return KnowledgeCoverageReport(
        entries=sorted_entries,
        summary=KnowledgeCoverageSummary(
            entity_type_count=len(sorted_entries),
            low_coverage_entity_type_count=sum(
                1 for entry in sorted_entries if entry.low_coverage_warning is not None
            ),
        ),
        note=(
            "knowledge coverage aggregates governed annotation availability by "
            "result-entity family and explicitly warns when sparse pathway, PTM-site, "
            "or regulator coverage should downgrade biological interpretation"
        ),
    )


def render_knowledge_coverage_tsv(
    entries: tuple[KnowledgeCoverageEntry, ...],
) -> str:
    """Render knowledge coverage rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_type",
            "total_count",
            "annotated_count",
            "coverage_fraction",
            "low_coverage_warning",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.entity_type.value,
                entry.total_count,
                entry.annotated_count,
                _format_fraction(entry.coverage_fraction),
                entry.low_coverage_warning or "",
            )
        )
    return handle.getvalue()


def _normalize_packs(packs: AnnotationPack | tuple[AnnotationPack, ...]) -> tuple[AnnotationPack, ...]:
    if isinstance(packs, AnnotationPack):
        return (packs,)
    return packs


def _merge_annotation_packs(packs: tuple[AnnotationPack, ...]) -> AnnotationPack:
    if not packs:
        return AnnotationPack(
            source_path="knowledge-coverage-empty-pack",
            pack_name="knowledge-coverage-empty-pack",
            summary=AnnotationPackSummary(
                protein_feature_count=0,
                pathway_count=0,
                complex_count=0,
                compartment_count=0,
                drug_target_count=0,
                disease_term_count=0,
                kinase_substrate_count=0,
                ortholog_count=0,
            ),
        )

    protein_features = _dedupe_records(
        (
            feature
            for pack in packs
            for feature in pack.protein_features
        ),
        key_fn=lambda feature: feature.protein_ref,
    )
    pathways = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.pathways
        ),
        key_fn=lambda record: (
            record.pathway_id,
            record.member_kind.value,
            record.member_id,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    complexes = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.complexes
        ),
        key_fn=lambda record: (
            record.complex_id,
            record.member_kind.value,
            record.member_id,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    compartments = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.compartments
        ),
        key_fn=lambda record: (
            record.protein_ref,
            record.context_kind.value,
            record.context_id,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    drug_targets = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.drug_targets
        ),
        key_fn=lambda record: (
            record.protein_ref,
            record.context_kind.value,
            record.context_id,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    disease_terms = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.disease_terms
        ),
        key_fn=lambda record: (
            record.protein_ref,
            record.context_kind.value,
            record.context_id,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    kinase_substrates = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.kinase_substrates
        ),
        key_fn=lambda record: (
            record.regulator,
            record.site_key,
            record.source_accession or "",
            record.source_name or "",
        ),
    )
    orthologs = _dedupe_records(
        (
            record
            for pack in packs
            for record in pack.orthologs
        ),
        key_fn=lambda record: (
            record.source_species,
            record.source_protein_ref,
            record.target_species,
            record.target_protein_ref,
        ),
    )
    return AnnotationPack(
        source_path="knowledge-coverage-merged-pack",
        pack_name="knowledge-coverage-merged-pack",
        protein_features=protein_features,
        pathways=pathways,
        complexes=complexes,
        compartments=compartments,
        drug_targets=drug_targets,
        disease_terms=disease_terms,
        kinase_substrates=kinase_substrates,
        orthologs=orthologs,
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


def _annotated_count(
    *,
    entity_set: KnowledgeCoverageEntitySet,
    merged_pack: AnnotationPack,
    pathway_ids: set[str],
    regulator_ids: set[str],
) -> int:
    if entity_set.entity_type is KnowledgeCoverageEntityType.PROTEIN:
        resolved_entries = resolve_protein_ids(entity_set.entity_ids, merged_pack)
        return len(
            {
                entry.input_id
                for entry in resolved_entries
                if entry.resolution_status
                not in {
                    ProteinIdentityResolutionStatus.UNRESOLVED,
                    ProteinIdentityResolutionStatus.AMBIGUOUS_ALIAS,
                }
            }
        )
    if entity_set.entity_type is KnowledgeCoverageEntityType.PATHWAY:
        return sum(1 for entity_id in entity_set.entity_ids if entity_id in pathway_ids)
    if entity_set.entity_type is KnowledgeCoverageEntityType.PTM_SITE:
        report = resolve_kinase_substrates(entity_set.entity_ids, merged_pack)
        return report.summary.resolved_site_count
    return sum(1 for entity_id in entity_set.entity_ids if entity_id.strip().casefold() in regulator_ids)


def _low_coverage_warning(
    *,
    entity_type: KnowledgeCoverageEntityType,
    coverage_fraction: float,
    policy: KnowledgeCoveragePolicy,
) -> str | None:
    threshold_by_entity_type = {
        KnowledgeCoverageEntityType.PROTEIN: policy.protein_min_coverage_fraction,
        KnowledgeCoverageEntityType.PATHWAY: policy.pathway_min_coverage_fraction,
        KnowledgeCoverageEntityType.PTM_SITE: policy.ptm_site_min_coverage_fraction,
        KnowledgeCoverageEntityType.REGULATOR: policy.regulator_min_coverage_fraction,
    }
    threshold = threshold_by_entity_type[entity_type]
    if coverage_fraction >= threshold:
        return None
    if entity_type is KnowledgeCoverageEntityType.PATHWAY:
        return "low pathway annotation coverage downgrades biological interpretation"
    if entity_type is KnowledgeCoverageEntityType.PTM_SITE:
        return "low ptm-site annotation coverage downgrades biological interpretation"
    if entity_type is KnowledgeCoverageEntityType.REGULATOR:
        return "low regulator annotation coverage downgrades biological interpretation"
    return "low protein annotation coverage limits biological interpretation"


def _dedupe_records(
    records: object,
    *,
    key_fn: Callable[[RecordT], object],
) -> tuple[RecordT, ...]:
    seen: set[object] = set()
    deduplicated: list[RecordT] = []
    for record in records:
        key = key_fn(record)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(record)
    return tuple(deduplicated)


def _format_fraction(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")
