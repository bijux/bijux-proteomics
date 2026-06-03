# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Drug-target interpretation over explicit target annotations and pathway context."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation.biological_context_mapping import (
    BiologicalContextKind,
    BiologicalContextRecord,
)
from bijux_proteomics.interpretation.pathway_enrichment import (
    PathwayMemberKind,
    PathwayMembershipRecord,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationMappingReport,
)
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    QuantEntityLevel,
)
from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics_foundation import JsonModel


class DrugTargetRelationship(StrEnum):
    """Stable relationship labels preserved on interpreted drug-protein rows."""

    DIRECT_TARGET = "direct_target"
    INDIRECT_PATHWAY_NEIGHBOR = "indirect_pathway_neighbor"


class DrugTargetEvidenceTier(StrEnum):
    """Stable evidence tiers for one interpreted drug-protein relationship."""

    HIGH_EVIDENCE = "high_evidence"
    MODERATE_EVIDENCE = "moderate_evidence"
    LOW_EVIDENCE = "low_evidence"


class DrugTargetEffectDirection(StrEnum):
    """Observed effect direction preserved on one regulated protein result."""

    UP = "up"
    DOWN = "down"


class DrugTargetInterpretationPolicy(JsonModel):
    """Selection policy for interpreted drug-target relationships."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)


class DrugTargetInterpretationEntry(JsonModel):
    """One interpreted regulated protein linked to one explicit drug context."""

    model_config = ConfigDict(extra="forbid")

    drug_id: str = Field(..., min_length=1)
    drug_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    protein_ref: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    relationship: DrugTargetRelationship
    evidence_tier: DrugTargetEvidenceTier
    effect_direction: DrugTargetEffectDirection
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_direct_target_refs: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    supporting_pathway_names: tuple[str, ...] = Field(default_factory=tuple)
    annotation_evidence_values: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DrugTargetInterpretationSummary(JsonModel):
    """Stable summary over one drug-target interpretation run."""

    model_config = ConfigDict(extra="forbid")

    drug_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    direct_target_entry_count: int = Field(..., ge=0)
    indirect_pathway_neighbor_entry_count: int = Field(..., ge=0)
    high_evidence_entry_count: int = Field(..., ge=0)
    moderate_evidence_entry_count: int = Field(..., ge=0)
    low_evidence_entry_count: int = Field(..., ge=0)


class DrugTargetInterpretationReport(JsonModel):
    """Owned drug-target interpretation report over regulated proteins."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    policy: DrugTargetInterpretationPolicy
    entries: tuple[DrugTargetInterpretationEntry, ...] = Field(default_factory=tuple)
    summary: DrugTargetInterpretationSummary
    note: str = Field(..., min_length=1)


class _ChangedPathwayState(TypedDict):
    pathway_name: str | None
    members: set[str]


class _IndirectDrugSupport(TypedDict):
    drug_name: str | None
    source_name: str | None
    source_accession: str | None
    direct_targets: set[str]
    pathway_ids: set[str]
    pathway_names: set[str]


def build_drug_target_interpretation_report(
    table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    context_records: tuple[BiologicalContextRecord, ...],
    *,
    pathway_records: tuple[PathwayMembershipRecord, ...] = (),
    annotation_report: ProteinAnnotationMappingReport | None = None,
    policy: DrugTargetInterpretationPolicy | None = None,
) -> DrugTargetInterpretationReport:
    """Interpret regulated proteins as explicit drug targets or pathway neighbors."""

    if table.entity_level is not QuantEntityLevel.PROTEIN:
        raise ValueError(
            "drug-target interpretation requires a protein-level quantification table"
        )

    active_policy = policy or DrugTargetInterpretationPolicy()
    drug_target_records = tuple(
        record
        for record in context_records
        if record.context_kind is BiologicalContextKind.DRUG_TARGET
    )
    if not drug_target_records:
        raise ValueError(
            "drug-target interpretation requires explicit drug_target context records"
        )

    changed_effects = _select_changed_protein_effects(
        table,
        differential_report,
        policy=active_policy,
    )
    gene_symbol_by_protein = _gene_symbol_by_protein_ref(annotation_report)
    direct_target_map = _group_direct_target_records(drug_target_records)
    entries: list[DrugTargetInterpretationEntry] = []
    direct_pairs: set[tuple[str, str]] = set()
    for drug_id, records in direct_target_map.items():
        first = records[0]
        evidence_values = _annotation_evidence_values(records)
        for protein_ref in sort_strings(
            tuple(
                canonicalize_protein_reference(record.protein_ref)
                for record in records
                if canonicalize_protein_reference(record.protein_ref) in changed_effects
            )
        ):
            effect = changed_effects[protein_ref]
            direct_pairs.add((drug_id, protein_ref))
            entries.append(
                DrugTargetInterpretationEntry(
                    drug_id=drug_id,
                    drug_name=first.context_name,
                    source_name=first.source_name,
                    source_accession=first.source_accession,
                    protein_ref=protein_ref,
                    gene_symbol=gene_symbol_by_protein.get(protein_ref),
                    relationship=DrugTargetRelationship.DIRECT_TARGET,
                    evidence_tier=_resolve_direct_evidence_tier(
                        source_name=first.source_name,
                        source_accession=first.source_accession,
                        evidence_values=evidence_values,
                    ),
                    effect_direction=_effect_direction(effect),
                    log2_fold_change=effect.log2_fold_change,
                    adjusted_p_value=effect.adjusted_p_value,
                    supporting_direct_target_refs=(protein_ref,),
                    annotation_evidence_values=evidence_values,
                    note=(
                        "regulated protein matched an explicit drug_target annotation "
                        "for this drug"
                    ),
                )
            )

    if pathway_records:
        pathway_index = _build_changed_pathway_index(
            pathway_records,
            gene_symbol_by_protein=gene_symbol_by_protein,
            changed_protein_refs=tuple(changed_effects),
        )
        indirect_support = _build_indirect_support(
            direct_target_map,
            direct_pairs=direct_pairs,
            changed_effects=changed_effects,
            pathway_index=pathway_index,
        )
        for key in sorted(indirect_support):
            support = indirect_support[key]
            drug_id, protein_ref = key
            effect = changed_effects[protein_ref]
            entries.append(
                DrugTargetInterpretationEntry(
                    drug_id=drug_id,
                    drug_name=support["drug_name"],
                    source_name=support["source_name"],
                    source_accession=support["source_accession"],
                    protein_ref=protein_ref,
                    gene_symbol=gene_symbol_by_protein.get(protein_ref),
                    relationship=DrugTargetRelationship.INDIRECT_PATHWAY_NEIGHBOR,
                    evidence_tier=_resolve_indirect_evidence_tier(
                        source_name=support["source_name"],
                        source_accession=support["source_accession"],
                        pathway_count=len(support["pathway_ids"]),
                        direct_target_count=len(support["direct_targets"]),
                    ),
                    effect_direction=_effect_direction(effect),
                    log2_fold_change=effect.log2_fold_change,
                    adjusted_p_value=effect.adjusted_p_value,
                    supporting_direct_target_refs=sort_strings(
                        tuple(support["direct_targets"])
                    ),
                    supporting_pathway_ids=sort_strings(tuple(support["pathway_ids"])),
                    supporting_pathway_names=sort_strings(
                        tuple(support["pathway_names"])
                    ),
                    annotation_evidence_values=_annotation_evidence_values(
                        direct_target_map[drug_id]
                    ),
                    note=(
                        "regulated protein shared pathway membership with one or more "
                        "explicit direct drug targets for this drug"
                    ),
                )
            )

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.drug_id,
                entry.relationship.value,
                entry.protein_ref,
            ),
        )
    )
    return DrugTargetInterpretationReport(
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
        policy=active_policy,
        entries=sorted_entries,
        summary=DrugTargetInterpretationSummary(
            drug_count=len({entry.drug_id for entry in sorted_entries}),
            entry_count=len(sorted_entries),
            direct_target_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.relationship is DrugTargetRelationship.DIRECT_TARGET
            ),
            indirect_pathway_neighbor_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.relationship is DrugTargetRelationship.INDIRECT_PATHWAY_NEIGHBOR
            ),
            high_evidence_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.evidence_tier is DrugTargetEvidenceTier.HIGH_EVIDENCE
            ),
            moderate_evidence_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.evidence_tier is DrugTargetEvidenceTier.MODERATE_EVIDENCE
            ),
            low_evidence_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.evidence_tier is DrugTargetEvidenceTier.LOW_EVIDENCE
            ),
        ),
        note=(
            "drug-target interpretation uses explicit drug_target annotations for "
            "direct calls and optional pathway memberships only for separate "
            "indirect_pathway_neighbor rows; proteins are never promoted to direct "
            "targets from shared pathway membership alone"
        ),
    )


def render_drug_target_interpretation_summary_tsv(
    report: DrugTargetInterpretationReport,
) -> str:
    """Render the compact drug-target interpretation summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "drug_count",
            "entry_count",
            "direct_target_entry_count",
            "indirect_pathway_neighbor_entry_count",
            "high_evidence_entry_count",
            "moderate_evidence_entry_count",
            "low_evidence_entry_count",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.drug_count,
            report.summary.entry_count,
            report.summary.direct_target_entry_count,
            report.summary.indirect_pathway_neighbor_entry_count,
            report.summary.high_evidence_entry_count,
            report.summary.moderate_evidence_entry_count,
            report.summary.low_evidence_entry_count,
        )
    )
    return buffer.getvalue()


def render_drug_target_interpretation_tsv(
    report: DrugTargetInterpretationReport,
) -> str:
    """Render interpreted drug-target and indirect-neighbor rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "drug_id",
            "drug_name",
            "source_name",
            "source_accession",
            "protein_ref",
            "gene_symbol",
            "relationship",
            "evidence_tier",
            "effect_direction",
            "log2_fold_change",
            "adjusted_p_value",
            "supporting_direct_target_refs",
            "supporting_pathway_ids",
            "supporting_pathway_names",
            "annotation_evidence_values",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.drug_id,
                entry.drug_name or "",
                entry.source_name or "",
                entry.source_accession or "",
                entry.protein_ref,
                entry.gene_symbol or "",
                entry.relationship.value,
                entry.evidence_tier.value,
                entry.effect_direction.value,
                f"{entry.log2_fold_change:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                ";".join(entry.supporting_direct_target_refs),
                ";".join(entry.supporting_pathway_ids),
                ";".join(entry.supporting_pathway_names),
                ";".join(entry.annotation_evidence_values),
                entry.note,
            )
        )
    return buffer.getvalue()


def _select_changed_protein_effects(
    table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    *,
    policy: DrugTargetInterpretationPolicy,
) -> dict[str, DifferentialAbundanceEntry]:
    selected: dict[str, DifferentialAbundanceEntry] = {}
    for entry in differential_report.entries:
        adjusted_p_value = entry.adjusted_p_value
        if adjusted_p_value is None or adjusted_p_value > policy.max_adjusted_p_value:
            continue
        if abs(entry.log2_fold_change) < policy.min_absolute_log2_fold_change:
            continue
        for protein_ref in table.entity_protein_refs.get(entry.entity_id, (entry.entity_id,)):
            canonical = canonicalize_protein_reference(protein_ref)
            best = selected.get(canonical)
            if best is None or _effect_precedes(entry, best):
                selected[canonical] = entry
    return selected


def _effect_precedes(
    candidate: DifferentialAbundanceEntry,
    incumbent: DifferentialAbundanceEntry,
) -> bool:
    candidate_p = 1.0 if candidate.adjusted_p_value is None else candidate.adjusted_p_value
    incumbent_p = 1.0 if incumbent.adjusted_p_value is None else incumbent.adjusted_p_value
    return (candidate_p, -abs(candidate.log2_fold_change), candidate.entity_id) < (
        incumbent_p,
        -abs(incumbent.log2_fold_change),
        incumbent.entity_id,
    )


def _group_direct_target_records(
    records: tuple[BiologicalContextRecord, ...],
) -> dict[str, tuple[BiologicalContextRecord, ...]]:
    grouped: dict[str, list[BiologicalContextRecord]] = {}
    for record in records:
        grouped.setdefault(record.context_id, []).append(record)
    return {
        key: tuple(
            sorted(
                group,
                key=lambda record: canonicalize_protein_reference(record.protein_ref),
            )
        )
        for key, group in grouped.items()
    }


def _annotation_evidence_values(
    records: tuple[BiologicalContextRecord, ...],
) -> tuple[str, ...]:
    return sort_strings(
        tuple(
            {
                record.evidence
                for record in records
                if record.evidence is not None
            }
        )
    )


def _effect_direction(entry: DifferentialAbundanceEntry) -> DrugTargetEffectDirection:
    if entry.log2_fold_change >= 0:
        return DrugTargetEffectDirection.UP
    return DrugTargetEffectDirection.DOWN


def _resolve_direct_evidence_tier(
    *,
    source_name: str | None,
    source_accession: str | None,
    evidence_values: tuple[str, ...],
) -> DrugTargetEvidenceTier:
    if (
        source_name is not None
        and source_accession is not None
        and any(value in {"curated", "reviewed"} for value in evidence_values)
    ):
        return DrugTargetEvidenceTier.HIGH_EVIDENCE
    if source_name is not None or source_accession is not None:
        return DrugTargetEvidenceTier.MODERATE_EVIDENCE
    return DrugTargetEvidenceTier.LOW_EVIDENCE


def _resolve_indirect_evidence_tier(
    *,
    source_name: str | None,
    source_accession: str | None,
    pathway_count: int,
    direct_target_count: int,
) -> DrugTargetEvidenceTier:
    if (
        source_name is not None
        and source_accession is not None
        and pathway_count >= 1
        and direct_target_count >= 1
    ):
        return DrugTargetEvidenceTier.MODERATE_EVIDENCE
    return DrugTargetEvidenceTier.LOW_EVIDENCE


def _gene_symbol_by_protein_ref(
    annotation_report: ProteinAnnotationMappingReport | None,
) -> dict[str, str]:
    if annotation_report is None:
        return {}
    return {
        canonicalize_protein_reference(entry.protein_ref): entry.gene_symbol
        for entry in annotation_report.result_entries
        if entry.gene_symbol is not None
    }


def _build_changed_pathway_index(
    pathway_records: tuple[PathwayMembershipRecord, ...],
    *,
    gene_symbol_by_protein: dict[str, str],
    changed_protein_refs: tuple[str, ...],
) -> dict[str, _ChangedPathwayState]:
    proteins_by_gene_symbol: dict[str, set[str]] = {}
    for protein_ref, gene_symbol in gene_symbol_by_protein.items():
        proteins_by_gene_symbol.setdefault(gene_symbol, set()).add(protein_ref)
    changed_set = {canonicalize_protein_reference(protein_ref) for protein_ref in changed_protein_refs}
    pathway_index: dict[str, _ChangedPathwayState] = {}
    for record in pathway_records:
        if record.member_kind is PathwayMemberKind.PROTEIN:
            member_refs = {
                canonicalize_protein_reference(record.member_id),
            }
        else:
            member_refs = proteins_by_gene_symbol.get(record.member_id, set())
        changed_members = tuple(
            sorted(protein_ref for protein_ref in member_refs if protein_ref in changed_set)
        )
        if not changed_members:
            continue
        pathway_state = pathway_index.setdefault(
            record.pathway_id,
            {
                "pathway_name": record.pathway_name,
                "members": set(),
            },
        )
        pathway_state["members"].update(changed_members)
    return pathway_index


def _build_indirect_support(
    direct_target_map: dict[str, tuple[BiologicalContextRecord, ...]],
    *,
    direct_pairs: set[tuple[str, str]],
    changed_effects: dict[str, DifferentialAbundanceEntry],
    pathway_index: dict[str, _ChangedPathwayState],
) -> dict[tuple[str, str], _IndirectDrugSupport]:
    support: dict[tuple[str, str], _IndirectDrugSupport] = {}
    for drug_id, records in direct_target_map.items():
        first = records[0]
        direct_refs = {
            canonicalize_protein_reference(record.protein_ref)
            for record in records
            if canonicalize_protein_reference(record.protein_ref) in changed_effects
        }
        if not direct_refs:
            continue
        for pathway_id, pathway_state in pathway_index.items():
            pathway_members = pathway_state["members"]
            direct_members = tuple(sorted(direct_refs.intersection(pathway_members)))
            if not direct_members:
                continue
            for protein_ref in sorted(pathway_members):
                key = (drug_id, protein_ref)
                if key in direct_pairs:
                    continue
                entry_support = support.setdefault(
                    key,
                    {
                        "drug_name": first.context_name,
                        "source_name": first.source_name,
                        "source_accession": first.source_accession,
                        "direct_targets": set(),
                        "pathway_ids": set(),
                        "pathway_names": set(),
                    },
                )
                entry_support["direct_targets"].update(direct_members)
                entry_support["pathway_ids"].add(pathway_id)
                if pathway_state["pathway_name"] is not None:
                    entry_support["pathway_names"].add(pathway_state["pathway_name"])
    return support


__all__ = [
    "DrugTargetEffectDirection",
    "DrugTargetEvidenceTier",
    "DrugTargetInterpretationEntry",
    "DrugTargetInterpretationPolicy",
    "DrugTargetInterpretationReport",
    "DrugTargetInterpretationSummary",
    "DrugTargetRelationship",
    "build_drug_target_interpretation_report",
    "render_drug_target_interpretation_summary_tsv",
    "render_drug_target_interpretation_tsv",
]
