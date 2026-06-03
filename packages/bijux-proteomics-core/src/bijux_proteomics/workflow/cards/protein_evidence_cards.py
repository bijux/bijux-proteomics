# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structured final-protein evidence cards over biological result bundles."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.card_schema import (
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    render_standard_card_row,
)
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.domain.semantic_ids import build_protein_card_id
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.protein_coverage import (
    build_protein_coverage_report,
)
from bijux_proteomics.interpretation import (
    BiologicalContextKind,
    BiologicalContextMappingReport,
    ComplexEnrichmentEntry,
    ComplexEnrichmentReport,
    PathwayEnrichmentEntry,
    PathwayEnrichmentReport,
    ProteinAnnotationMappingReport,
    ProteinAnnotationResultEntry,
    ProteinAnnotationStatus,
)
from bijux_proteomics.ptm import PtmEvidenceCardReport
from bijux_proteomics.quantification import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
    MissingValueKind,
    QuantValue,
)
from bijux_proteomics.review import (
    EvidenceGraphFinalResultEntry,
    FinalClaimEvidenceTier,
    ProteinEvidenceSummaryReport,
    ProteomicsEvidenceNodeKind,
    query_protein_evidence_summary,
)
from bijux_proteomics.sequences import (
    NormalizedProteinRecord,
    ProteinFunctionalRegionEvidence,
    ProteinFunctionalRegionKind,
    ProteinIdentityLevel,
    ProteinIdentityReference,
    ProteinIdentityResolutionEntry,
    ProteinPeptideRegionContextReport,
    ProteinPeptideRegionReference,
    ProteinRegionContextRecord,
    ProteogenomicPeptideReference,
    ProteogenomicPeptideSupportEntry,
    ProteogenomicVariantPeptideRecord,
    build_protein_identity_resolution_report,
    build_protein_peptide_region_context_report,
    build_proteogenomic_peptide_support_report,
)
from bijux_proteomics.workflow.reports.biological_result_graph import (
    BiologicalResultGraphReport,
)
from bijux_proteomics_foundation import JsonModel


class ProteinEvidenceCardSelectionPolicy(JsonModel):
    """Selection policy copied onto final-protein evidence-card reports."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)


class ProteinEvidenceCardTier(StrEnum):
    """Evidence-support tiers over final protein result cards."""

    HIGH_SUPPORT = "high_support"
    MODERATE_SUPPORT = "moderate_support"
    REVIEW = "review"


class ProteinEvidenceCardWarningCode(StrEnum):
    """Stable warning codes preserved on one final protein card."""

    NOT_SIGNIFICANT = "not_significant"
    ANNOTATION_UNMAPPED = "annotation_unmapped"
    SHARED_PEPTIDE_ONLY = "shared_peptide_only"
    LOW_UNIQUE_PEPTIDE_SUPPORT = "low_unique_peptide_support"
    LOW_SEQUENCE_COVERAGE = "low_sequence_coverage"
    CONDITION_MISSINGNESS = "condition_missingness"


class ProteinEvidenceCardWarning(JsonModel):
    """One review warning attached to a final protein card."""

    model_config = ConfigDict(extra="forbid")

    code: ProteinEvidenceCardWarningCode
    message: str = Field(..., min_length=1)


class ProteinEvidenceCardAnnotation(JsonModel):
    """Annotation payload preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    annotation_status: ProteinAnnotationStatus
    gene_symbol: str | None = None
    description: str | None = None
    organism: str | None = None
    annotation_identifiers: tuple[str, ...] = Field(default_factory=tuple)
    accession_aliases: tuple[str, ...] = Field(default_factory=tuple)
    custom_annotation: dict[str, str] = Field(default_factory=dict)


class ProteinEvidenceCardCoverage(JsonModel):
    """Sequence-backed coverage summary preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    coverage_protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=0)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinEvidenceCardSampleValue(JsonModel):
    """One sample-level abundance cell on a final protein card."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_feature_count: int = Field(..., ge=0)


class ProteinEvidenceCardQuantification(JsonModel):
    """Quantification evidence preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    sample_values: tuple[ProteinEvidenceCardSampleValue, ...] = Field(
        default_factory=tuple
    )
    observed_sample_count: int = Field(..., ge=0)
    zero_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    filtered_sample_count: int = Field(..., ge=0)


class ProteinEvidenceCardDifferentialResult(JsonModel):
    """Differential result preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    observations_a: int = Field(..., ge=0)
    observations_b: int = Field(..., ge=0)
    complete_pair_count: int = Field(..., ge=0)
    mean_log2_abundance_a: float
    mean_log2_abundance_b: float
    log2_fold_change: float
    p_value: float = Field(..., ge=0.0, le=1.0)
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    standard_error: float | None = Field(default=None, ge=0.0)
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    effect_size_cohens_d: float | None = None
    uncertainty_note: str | None = None


class ProteinEvidenceCardContextEntry(JsonModel):
    """User-supplied biological context preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    context_kind: BiologicalContextKind
    context_id: str = Field(..., min_length=1)
    context_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None


class ProteinEvidenceCardPathwayEntryKind(StrEnum):
    """Functional-entry kinds preserved on one final protein card."""

    PATHWAY = "pathway"
    COMPLEX = "complex"


class ProteinEvidenceCardPathwayEntry(JsonModel):
    """Enriched pathway or complex evidence preserved on one final protein card."""

    model_config = ConfigDict(extra="forbid")

    entry_kind: ProteinEvidenceCardPathwayEntryKind
    entry_id: str = Field(..., min_length=1)
    entry_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    enrichment_ratio: float | None = Field(default=None, ge=0.0)


class ProteinEvidenceCard(JsonModel):
    """One structured object for one final protein result."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    graph_claim_node_id: str = Field(..., min_length=1)
    graph_subject_node_id: str = Field(..., min_length=1)
    graph_subject_node_kind: ProteomicsEvidenceNodeKind
    graph_support_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    protein_group_id: str = Field(..., min_length=1)
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    identity_level: ProteinIdentityLevel
    identity_reason: str = Field(..., min_length=1)
    annotation: ProteinEvidenceCardAnnotation
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage: ProteinEvidenceCardCoverage
    quantification: ProteinEvidenceCardQuantification
    differential_result: ProteinEvidenceCardDifferentialResult
    context_terms: tuple[ProteinEvidenceCardContextEntry, ...] = Field(
        default_factory=tuple
    )
    pathways: tuple[ProteinEvidenceCardPathwayEntry, ...] = Field(default_factory=tuple)
    functional_regions: tuple[ProteinFunctionalRegionEvidence, ...] = Field(
        default_factory=tuple
    )
    proteogenomic_support: ProteogenomicPeptideSupportEntry | None = None
    ptm_sites: tuple[str, ...] = Field(default_factory=tuple)
    significant: bool
    evidence_tier: ProteinEvidenceCardTier
    warnings: tuple[ProteinEvidenceCardWarning, ...] = Field(default_factory=tuple)


class ProteinEvidenceCardSummary(JsonModel):
    """Stable summary over one final-protein evidence-card pass."""

    model_config = ConfigDict(extra="forbid")

    protein_result_count: int = Field(..., ge=0)
    significant_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    pathway_annotated_card_count: int = Field(..., ge=0)
    context_annotated_card_count: int = Field(..., ge=0)
    functional_region_annotated_card_count: int = Field(..., ge=0)
    proteogenomic_annotated_card_count: int = Field(..., ge=0)
    ptm_annotated_card_count: int = Field(..., ge=0)


class ProteinEvidenceCardReport(JsonModel):
    """Stable final-protein evidence-card report over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    selection_policy: ProteinEvidenceCardSelectionPolicy
    summary: ProteinEvidenceCardSummary
    cards: tuple[ProteinEvidenceCard, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class _PreparedProteinCard(TypedDict):
    final_entry: EvidenceGraphFinalResultEntry
    differential_entry: DifferentialAbundanceEntry
    graph_summary: ProteinEvidenceSummaryReport
    representative_protein_ref: str
    protein_refs: tuple[str, ...]
    annotation: ProteinEvidenceCardAnnotation
    peptides: tuple[str, ...]
    unique_peptide_count: int
    shared_peptide_count: int
    coverage: ProteinEvidenceCardCoverage
    quantification: ProteinEvidenceCardQuantification
    contexts: tuple[ProteinEvidenceCardContextEntry, ...]
    pathways: tuple[ProteinEvidenceCardPathwayEntry, ...]
    functional_regions: tuple[ProteinFunctionalRegionEvidence, ...]
    significant: bool
    warnings: tuple[ProteinEvidenceCardWarning, ...]


def build_protein_evidence_card_report(
    graph_report: BiologicalResultGraphReport,
    quant_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    annotation_report: ProteinAnnotationMappingReport,
    *,
    protein_sequences: dict[str, str],
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    variant_protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...]
    | None = None,
    selection_policy: ProteinEvidenceCardSelectionPolicy,
    sample_conditions: dict[str, str | None] | None = None,
    context_mapping_report: BiologicalContextMappingReport | None = None,
    pathway_enrichment_report: PathwayEnrichmentReport | None = None,
    complex_enrichment_report: ComplexEnrichmentReport | None = None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...]
    | None = None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None = None,
) -> ProteinEvidenceCardReport:
    """Build one structured card per final protein result."""

    values_by_entity = _group_values_by_entity(quant_table.values)
    protein_peptides = {
        entity_id: tuple(
            sorted(set(quant_table.entity_member_peptides.get(entity_id, ())))
        )
        for entity_id in quant_table.entity_ids
    }
    peptide_membership_counts = Counter(
        peptide for peptides in protein_peptides.values() for peptide in peptides
    )
    coverage_by_protein = _build_coverage_by_protein(
        quant_table,
        protein_sequences=protein_sequences,
    )
    annotations_by_entity = _group_annotations_by_entity(annotation_report)
    context_by_protein = _group_context_entries_by_protein(context_mapping_report)
    pathway_by_member = _group_pathway_entries_by_member(
        pathway_enrichment_report,
        complex_enrichment_report,
    )
    functional_regions_by_protein = _group_functional_regions_by_protein(
        _build_peptide_region_context_report(
            quant_table,
            protein_sequences=protein_sequences,
            protein_region_context_records=protein_region_context_records,
        )
    )
    ptm_sites_by_protein = _group_ptm_sites_by_protein(ptm_evidence_card_report)
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    final_entries = tuple(
        entry
        for entry in graph_report.final_results.entries
        if entry.subject_node_kind is ProteomicsEvidenceNodeKind.PROTEIN
    )
    prepared_cards: list[_PreparedProteinCard] = []
    for final_entry in sorted(final_entries, key=lambda entry: entry.subject_node_ref):
        differential_entry = differential_by_entity.get(final_entry.subject_node_ref)
        if differential_entry is None:
            continue
        protein_refs = quant_table.entity_protein_refs.get(
            differential_entry.entity_id,
            (),
        ) or (differential_entry.entity_id,)
        annotation_entries = annotations_by_entity.get(differential_entry.entity_id, ())
        representative_protein_ref = _select_representative_protein_ref(
            protein_refs,
            annotation_entries=annotation_entries,
            protein_sequences=protein_sequences,
        )
        peptides = protein_peptides.get(differential_entry.entity_id, ())
        unique_peptide_count = sum(
            1 for peptide in peptides if peptide_membership_counts.get(peptide, 0) == 1
        )
        shared_peptide_count = len(peptides) - unique_peptide_count
        coverage = coverage_by_protein.get(
            representative_protein_ref,
            ProteinEvidenceCardCoverage(
                coverage_protein_ref=representative_protein_ref,
                residue_count=len(
                    protein_sequences.get(representative_protein_ref, "")
                ),
                covered_residue_count=0,
                coverage_fraction=0.0,
                covered_peptides=(),
            ),
        )
        annotation = _build_annotation_payload(
            representative_protein_ref,
            annotation_entries=annotation_entries,
        )
        quantification = _build_quantification_payload(
            values_by_entity.get(differential_entry.entity_id, ()),
            sample_conditions={} if sample_conditions is None else sample_conditions,
        )
        significant = _entry_is_significant(
            differential_entry,
            policy=selection_policy,
        )
        contexts = _select_context_entries(
            protein_refs,
            by_protein=context_by_protein,
        )
        pathways = _select_pathway_entries(
            protein_refs,
            annotation_entries=annotation_entries,
            by_member=pathway_by_member,
        )
        functional_regions = _select_functional_regions(
            protein_refs,
            by_protein=functional_regions_by_protein,
        )
        graph_summary = query_protein_evidence_summary(
            graph_report.graph,
            protein_id=final_entry.subject_node_ref,
        )
        warnings = _build_warnings(
            annotation=annotation,
            coverage=coverage,
            differential_entry=differential_entry,
            significant=significant,
            unique_peptide_count=unique_peptide_count,
            peptide_count=len(peptides),
        )
        prepared_cards.append(
            {
                "final_entry": final_entry,
                "differential_entry": differential_entry,
                "graph_summary": graph_summary,
                "representative_protein_ref": representative_protein_ref,
                "protein_refs": protein_refs,
                "annotation": annotation,
                "peptides": peptides,
                "unique_peptide_count": unique_peptide_count,
                "shared_peptide_count": shared_peptide_count,
                "coverage": coverage,
                "quantification": quantification,
                "contexts": contexts,
                "pathways": pathways,
                "functional_regions": functional_regions,
                "significant": significant,
                "warnings": warnings,
            }
        )

    identity_by_entity = _build_identity_entries_by_entity(
        prepared_cards,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
    )
    proteogenomic_support_by_entity = _build_proteogenomic_support_by_entity(
        prepared_cards,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
        variant_protein_records=variant_protein_records,
        variant_peptide_records=variant_peptide_records,
    )
    cards: list[ProteinEvidenceCard] = []
    for prepared_card in prepared_cards:
        differential_entry = prepared_card["differential_entry"]
        final_entry = prepared_card["final_entry"]
        identity_entry = identity_by_entity.get(differential_entry.entity_id)
        cards.append(
            ProteinEvidenceCard(
                card_id=_build_card_id(differential_entry.entity_id),
                graph_claim_node_id=final_entry.claim_node_id,
                graph_subject_node_id=final_entry.subject_node_id,
                graph_subject_node_kind=final_entry.subject_node_kind,
                graph_support_node_ids=_graph_support_node_ids(
                    prepared_card["graph_summary"]
                ),
                graph_source_row_refs=final_entry.source_row_refs,
                protein_group_id=differential_entry.entity_id,
                representative_protein_ref=prepared_card["representative_protein_ref"],
                protein_refs=prepared_card["protein_refs"],
                identity_level=(
                    ProteinIdentityLevel.AMBIGUOUS
                    if identity_entry is None
                    else identity_entry.identity_level
                ),
                identity_reason=(
                    "protein identity could not be resolved because no peptide-backed sequence context was available"
                    if identity_entry is None
                    else identity_entry.identity_reason
                ),
                annotation=prepared_card["annotation"],
                peptides=prepared_card["peptides"],
                peptide_count=len(prepared_card["peptides"]),
                unique_peptide_count=prepared_card["unique_peptide_count"],
                shared_peptide_count=prepared_card["shared_peptide_count"],
                coverage=prepared_card["coverage"],
                quantification=prepared_card["quantification"],
                differential_result=_build_differential_payload(differential_entry),
                context_terms=prepared_card["contexts"],
                pathways=prepared_card["pathways"],
                functional_regions=prepared_card["functional_regions"],
                proteogenomic_support=proteogenomic_support_by_entity.get(
                    differential_entry.entity_id
                ),
                ptm_sites=_select_ptm_sites(
                    prepared_card["protein_refs"],
                    by_protein=ptm_sites_by_protein,
                ),
                significant=prepared_card["significant"],
                evidence_tier=_graph_evidence_tier(final_entry.evidence_tier),
                warnings=prepared_card["warnings"],
            )
        )

    return ProteinEvidenceCardReport(
        selection_policy=selection_policy,
        summary=ProteinEvidenceCardSummary(
            protein_result_count=len(cards),
            significant_card_count=sum(1 for card in cards if card.significant),
            warning_card_count=sum(1 for card in cards if card.warnings),
            pathway_annotated_card_count=sum(1 for card in cards if card.pathways),
            context_annotated_card_count=sum(1 for card in cards if card.context_terms),
            functional_region_annotated_card_count=sum(
                1 for card in cards if card.functional_regions
            ),
            proteogenomic_annotated_card_count=sum(
                1 for card in cards if card.proteogenomic_support is not None
            ),
            ptm_annotated_card_count=sum(1 for card in cards if card.ptm_sites),
        ),
        cards=tuple(cards),
        note=(
            "protein evidence cards preserve one structured object per final protein result, "
            "derive final claim identity and evidence tiers from the canonical review graph, "
            "carry annotation, peptide membership, coverage, quantification, differential, "
            "context, pathway, functional-region, proteogenomic peptide-support, and warning "
            "evidence together, and give "
            "biological reporting one stable graph-backed table source instead of ad hoc "
            "final-protein summaries"
        ),
    )


def render_protein_evidence_card_summary_tsv(report: ProteinEvidenceCardReport) -> str:
    """Render the protein-card summary ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("protein_result_count", report.summary.protein_result_count))
    writer.writerow(("significant_card_count", report.summary.significant_card_count))
    writer.writerow(("warning_card_count", report.summary.warning_card_count))
    writer.writerow(
        ("pathway_annotated_card_count", report.summary.pathway_annotated_card_count)
    )
    writer.writerow(
        ("context_annotated_card_count", report.summary.context_annotated_card_count)
    )
    writer.writerow(
        (
            "functional_region_annotated_card_count",
            report.summary.functional_region_annotated_card_count,
        )
    )
    writer.writerow(
        (
            "proteogenomic_annotated_card_count",
            report.summary.proteogenomic_annotated_card_count,
        )
    )
    writer.writerow(
        ("ptm_annotated_card_count", report.summary.ptm_annotated_card_count)
    )
    writer.writerow(
        ("max_adjusted_p_value", report.selection_policy.max_adjusted_p_value)
    )
    writer.writerow(
        (
            "min_absolute_log2_fold_change",
            report.selection_policy.min_absolute_log2_fold_change,
        )
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_protein_evidence_card_tsv(report: ProteinEvidenceCardReport) -> str:
    """Render final protein cards as a flat TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "card_kind",
            "subject_kind",
            "subject_id",
            "subject_label",
            "claim",
            "evidence_for",
            "evidence_against",
            "confidence",
            "warning_codes",
            "source_ids",
            "graph_claim_node_id",
            "graph_subject_node_id",
            "graph_subject_node_kind",
            "graph_support_node_ids",
            "graph_source_row_refs",
            "protein_group_id",
            "representative_protein_ref",
            "protein_refs",
            "identity_level",
            "identity_reason",
            "gene_symbol",
            "annotation_status",
            "peptides",
            "peptide_count",
            "unique_peptide_count",
            "shared_peptide_count",
            "coverage_fraction",
            "covered_residue_count",
            "residue_count",
            "observed_sample_count",
            "missing_sample_count",
            "condition_a",
            "condition_b",
            "log2_fold_change",
            "adjusted_p_value",
            "significant",
            "evidence_tier",
            "pathway_ids",
            "context_ids",
            "functional_regions",
            "proteogenomic_support_class",
            "proteogenomic_support_reason",
            "proteogenomic_reference_only_peptides",
            "proteogenomic_variant_only_peptides",
            "proteogenomic_shared_peptides",
            "proteogenomic_ambiguous_peptides",
            "proteogenomic_variant_protein_refs",
            "ptm_sites",
        )
    )
    for card in report.cards:
        standard_card = _build_standard_card_entry(card)
        writer.writerow(
            (
                *render_standard_card_row(standard_card),
                card.graph_claim_node_id,
                card.graph_subject_node_id,
                card.graph_subject_node_kind.value,
                ";".join(card.graph_support_node_ids),
                ";".join(card.graph_source_row_refs),
                card.protein_group_id,
                card.representative_protein_ref,
                ";".join(card.protein_refs),
                card.identity_level.value,
                card.identity_reason,
                ""
                if card.annotation.gene_symbol is None
                else card.annotation.gene_symbol,
                card.annotation.annotation_status.value,
                ";".join(card.peptides),
                card.peptide_count,
                card.unique_peptide_count,
                card.shared_peptide_count,
                card.coverage.coverage_fraction,
                card.coverage.covered_residue_count,
                card.coverage.residue_count,
                card.quantification.observed_sample_count,
                card.quantification.missing_sample_count,
                card.differential_result.condition_a,
                card.differential_result.condition_b,
                card.differential_result.log2_fold_change,
                ""
                if card.differential_result.adjusted_p_value is None
                else card.differential_result.adjusted_p_value,
                str(card.significant).lower(),
                card.evidence_tier.value,
                ";".join(entry.entry_id for entry in card.pathways),
                ";".join(
                    f"{entry.context_kind.value}:{entry.context_id}"
                    for entry in card.context_terms
                ),
                ";".join(
                    f"{region.region_kind.value}:{region.label}@{region.start}-{region.end}"
                    for region in card.functional_regions
                ),
                ""
                if card.proteogenomic_support is None
                else card.proteogenomic_support.support_class.value,
                ""
                if card.proteogenomic_support is None
                else card.proteogenomic_support.support_reason,
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.reference_only_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.variant_only_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.shared_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.ambiguous_peptides),
                ""
                if card.proteogenomic_support is None
                else ";".join(card.proteogenomic_support.matched_variant_protein_refs),
                ";".join(card.ptm_sites),
            )
        )
    return handle.getvalue()


def export_protein_evidence_card_summary_tsv(
    report: ProteinEvidenceCardReport,
    path: Path,
) -> None:
    """Write the protein-card summary ledger to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_evidence_card_summary_tsv(report))


def export_protein_evidence_card_tsv(
    report: ProteinEvidenceCardReport,
    path: Path,
) -> None:
    """Write final protein cards to one stable TSV artifact."""

    write_output_table_tsv(path, render_protein_evidence_card_tsv(report))


def _group_values_by_entity(
    values: tuple[QuantValue, ...],
) -> dict[str, tuple[QuantValue, ...]]:
    grouped: dict[str, list[QuantValue]] = defaultdict(list)
    for value in values:
        grouped[value.entity_id].append(value)
    return {
        entity_id: tuple(sorted(entries, key=lambda entry: entry.sample_id))
        for entity_id, entries in grouped.items()
    }


def _build_annotation_payload(
    representative_protein_ref: str,
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
) -> ProteinEvidenceCardAnnotation:
    annotated_entries = tuple(
        entry
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    )
    primary_entry = (
        next(
            (
                entry
                for entry in annotated_entries
                if entry.protein_ref == representative_protein_ref
            ),
            None,
        )
        or (annotated_entries[0] if annotated_entries else None)
        or (annotation_entries[0] if annotation_entries else None)
    )
    if primary_entry is None:
        return ProteinEvidenceCardAnnotation(
            annotation_status=ProteinAnnotationStatus.UNMAPPED,
        )
    return ProteinEvidenceCardAnnotation(
        annotation_status=primary_entry.annotation_status,
        gene_symbol=primary_entry.gene_symbol,
        description=primary_entry.description,
        organism=primary_entry.organism,
        annotation_identifiers=tuple(
            sorted(
                {
                    entry.annotation_identifier
                    for entry in annotated_entries
                    if entry.annotation_identifier
                }
            )
        ),
        accession_aliases=tuple(
            sorted(
                {
                    alias
                    for entry in annotation_entries
                    for alias in entry.accession_aliases
                }
            )
        ),
        custom_annotation=dict(sorted(primary_entry.custom_annotation.items())),
    )


def _build_quantification_payload(
    values: tuple[QuantValue, ...],
    *,
    sample_conditions: dict[str, str | None],
) -> ProteinEvidenceCardQuantification:
    sample_values = tuple(
        ProteinEvidenceCardSampleValue(
            sample_id=value.sample_id,
            condition=sample_conditions.get(value.sample_id),
            abundance=value.abundance,
            missing_value_kind=value.missing_value_kind,
            source_feature_count=value.source_feature_count,
        )
        for value in values
    )
    return ProteinEvidenceCardQuantification(
        sample_values=sample_values,
        observed_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.OBSERVED
        ),
        zero_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.ZERO
        ),
        missing_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.NOT_OBSERVED
        ),
        filtered_sample_count=sum(
            1
            for value in sample_values
            if value.missing_value_kind is MissingValueKind.FILTERED
        ),
    )


def _build_differential_payload(
    entry: DifferentialAbundanceEntry,
) -> ProteinEvidenceCardDifferentialResult:
    return ProteinEvidenceCardDifferentialResult(
        condition_a=entry.condition_a,
        condition_b=entry.condition_b,
        observations_a=entry.observations_a,
        observations_b=entry.observations_b,
        complete_pair_count=entry.complete_pair_count,
        mean_log2_abundance_a=entry.mean_log2_abundance_a,
        mean_log2_abundance_b=entry.mean_log2_abundance_b,
        log2_fold_change=entry.log2_fold_change,
        p_value=entry.p_value,
        adjusted_p_value=entry.adjusted_p_value,
        standard_error=entry.standard_error,
        confidence_interval_low=entry.confidence_interval_low,
        confidence_interval_high=entry.confidence_interval_high,
        effect_size_cohens_d=entry.effect_size_cohens_d,
        uncertainty_note=entry.uncertainty_note,
    )


def _group_annotations_by_entity(
    report: ProteinAnnotationMappingReport,
) -> dict[str, tuple[ProteinAnnotationResultEntry, ...]]:
    grouped: dict[str, list[ProteinAnnotationResultEntry]] = defaultdict(list)
    for entry in report.result_entries:
        grouped[(entry.source_row_id or entry.protein_ref)].append(entry)
    return {
        entity_id: tuple(sorted(entries, key=lambda entry: entry.protein_ref))
        for entity_id, entries in grouped.items()
    }


def _group_context_entries_by_protein(
    report: BiologicalContextMappingReport | None,
) -> dict[str, tuple[ProteinEvidenceCardContextEntry, ...]]:
    if report is None:
        return {}
    grouped: dict[str, list[ProteinEvidenceCardContextEntry]] = defaultdict(list)
    for entry in report.term_entries:
        context_entry = ProteinEvidenceCardContextEntry(
            context_kind=entry.context_kind,
            context_id=entry.context_id,
            context_name=entry.context_name,
            source_name=entry.source_name,
            source_accession=entry.source_accession,
        )
        for protein_ref in entry.supporting_protein_refs:
            grouped[protein_ref].append(context_entry)
    return {
        protein_ref: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.context_kind.value, entry.context_id),
            )
        )
        for protein_ref, entries in grouped.items()
    }


def _group_pathway_entries_by_member(
    pathway_report: PathwayEnrichmentReport | None,
    complex_report: ComplexEnrichmentReport | None,
) -> dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]]:
    grouped: dict[str, list[ProteinEvidenceCardPathwayEntry]] = defaultdict(list)
    if pathway_report is not None:
        for entry in pathway_report.entries:
            card_entry = _pathway_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    if complex_report is not None:
        for entry in complex_report.entries:
            card_entry = _complex_card_entry(entry)
            for member_id in entry.foreground_member_ids:
                grouped[member_id].append(card_entry)
    return {
        member_id: tuple(
            sorted(
                entries,
                key=lambda entry: (entry.entry_kind.value, entry.entry_id),
            )
        )
        for member_id, entries in grouped.items()
    }


def _build_peptide_region_context_report(
    quant_table: LabelFreeQuantTable,
    *,
    protein_sequences: dict[str, str],
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None,
) -> ProteinPeptideRegionContextReport | None:
    if not protein_region_context_records:
        return None
    references = tuple(
        ProteinPeptideRegionReference(
            peptide_key=f"{protein_ref}:{peptide}",
            protein_ref=protein_ref,
            peptide_sequence=peptide,
        )
        for entity_id, peptides in quant_table.entity_member_peptides.items()
        for protein_ref in (
            quant_table.entity_protein_refs.get(entity_id, ()) or (entity_id,)
        )
        for peptide in sorted(set(peptides))
    )
    return build_protein_peptide_region_context_report(
        references,
        protein_sequences=protein_sequences,
        context_records=protein_region_context_records,
    )


def _build_identity_entries_by_entity(
    prepared_cards: list[_PreparedProteinCard],
    *,
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str],
) -> dict[str, ProteinIdentityResolutionEntry]:
    if not prepared_cards:
        return {}
    report = build_protein_identity_resolution_report(
        tuple(
            ProteinIdentityReference(
                evidence_key=prepared_card["differential_entry"].entity_id,
                target_protein_ref=prepared_card["representative_protein_ref"],
                candidate_protein_refs=prepared_card["protein_refs"],
                peptide_sequences=prepared_card["peptides"],
            )
            for prepared_card in prepared_cards
        ),
        protein_records=() if protein_records is None else protein_records,
        protein_sequences=protein_sequences,
    )
    return {entry.evidence_key: entry for entry in report.entries}


def _build_proteogenomic_support_by_entity(
    prepared_cards: list[_PreparedProteinCard],
    *,
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str],
    variant_protein_records: tuple[NormalizedProteinRecord, ...] | None,
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...] | None,
) -> dict[str, ProteogenomicPeptideSupportEntry]:
    if not prepared_cards or (
        not variant_protein_records and not variant_peptide_records
    ):
        return {}
    report = build_proteogenomic_peptide_support_report(
        tuple(
            ProteogenomicPeptideReference(
                evidence_key=prepared_card["differential_entry"].entity_id,
                peptide_sequences=prepared_card["peptides"],
                target_protein_refs=prepared_card["protein_refs"],
            )
            for prepared_card in prepared_cards
        ),
        reference_protein_records=() if protein_records is None else protein_records,
        reference_protein_sequences=protein_sequences,
        variant_protein_records=()
        if variant_protein_records is None
        else variant_protein_records,
        variant_peptide_records=()
        if variant_peptide_records is None
        else variant_peptide_records,
    )
    return {entry.evidence_key: entry for entry in report.entries}


def _group_functional_regions_by_protein(
    report: ProteinPeptideRegionContextReport | None,
) -> dict[str, tuple[ProteinFunctionalRegionEvidence, ...]]:
    if report is None:
        return {}
    grouped: dict[
        str,
        dict[tuple[str, str, int, int, str | None, str | None], set[str]],
    ] = defaultdict(dict)
    for entry in report.entries:
        for region in entry.functional_regions:
            key = (
                region.region_kind.value,
                region.label,
                region.start,
                region.end,
                region.source_name,
                region.source_accession,
            )
            grouped[entry.protein_ref].setdefault(key, set()).update(
                region.supporting_evidence_refs
            )
    return {
        protein_ref: tuple(
            ProteinFunctionalRegionEvidence(
                region_kind=ProteinFunctionalRegionKind(region_kind_value),
                label=label,
                start=start,
                end=end,
                source_name=source_name,
                source_accession=source_accession,
                supporting_evidence_refs=tuple(sorted(refs)),
            )
            for (
                region_kind_value,
                label,
                start,
                end,
                source_name,
                source_accession,
            ), refs in sorted(
                region_entries.items(),
                key=lambda item: (
                    item[0][0],
                    item[0][2],
                    item[0][3],
                    item[0][1],
                    item[0][4] or "",
                    item[0][5] or "",
                ),
            )
        )
        for protein_ref, region_entries in grouped.items()
    }


def _group_ptm_sites_by_protein(
    report: PtmEvidenceCardReport | None,
) -> dict[str, tuple[str, ...]]:
    if report is None:
        return {}
    grouped: dict[str, set[str]] = defaultdict(set)
    for card in report.cards:
        grouped[card.protein_ref].add(card.site_key)
    return {
        protein_ref: tuple(sorted(site_keys))
        for protein_ref, site_keys in grouped.items()
    }


def _select_ptm_sites(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                site_key
                for protein_ref in protein_refs
                for site_key in by_protein.get(protein_ref, ())
            }
        )
    )


def _select_functional_regions(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[ProteinFunctionalRegionEvidence, ...]],
) -> tuple[ProteinFunctionalRegionEvidence, ...]:
    merged: dict[tuple[str, str, int, int, str | None, str | None], set[str]] = {}
    for protein_ref in protein_refs:
        for region in by_protein.get(protein_ref, ()):
            key = (
                region.region_kind.value,
                region.label,
                region.start,
                region.end,
                region.source_name,
                region.source_accession,
            )
            merged.setdefault(key, set()).update(region.supporting_evidence_refs)
    return tuple(
        ProteinFunctionalRegionEvidence(
            region_kind=ProteinFunctionalRegionKind(region_kind_value),
            label=label,
            start=start,
            end=end,
            source_name=source_name,
            source_accession=source_accession,
            supporting_evidence_refs=tuple(sorted(refs)),
        )
        for (
            region_kind_value,
            label,
            start,
            end,
            source_name,
            source_accession,
        ), refs in sorted(
            merged.items(),
            key=lambda item: (
                item[0][0],
                item[0][2],
                item[0][3],
                item[0][1],
                item[0][4] or "",
                item[0][5] or "",
            ),
        )
    )


def _pathway_card_entry(
    entry: PathwayEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.PATHWAY,
        entry_id=entry.pathway_id,
        entry_name=entry.pathway_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )


def _complex_card_entry(
    entry: ComplexEnrichmentEntry,
) -> ProteinEvidenceCardPathwayEntry:
    return ProteinEvidenceCardPathwayEntry(
        entry_kind=ProteinEvidenceCardPathwayEntryKind.COMPLEX,
        entry_id=entry.complex_id,
        entry_name=entry.complex_name,
        source_name=entry.source_name,
        source_accession=entry.source_accession,
        adjusted_p_value=entry.adjusted_p_value,
        enrichment_ratio=entry.enrichment_ratio,
    )


def _build_coverage_by_protein(
    quant_table: LabelFreeQuantTable,
    *,
    protein_sequences: dict[str, str],
) -> dict[str, ProteinEvidenceCardCoverage]:
    synthetic_records: list[PsmRecord] = []
    for entity_id, peptides in quant_table.entity_member_peptides.items():
        protein_refs = quant_table.entity_protein_refs.get(entity_id, ()) or (
            entity_id,
        )
        for peptide_index, peptide in enumerate(sorted(set(peptides)), start=1):
            synthetic_records.append(
                PsmRecord(
                    spectrum_id=f"{entity_id}:coverage:{peptide_index}",
                    peptide=peptide,
                    peptide_sequence=peptide,
                    canonical_peptide=peptide,
                    charge=2,
                    score=1.0,
                    q_value=0.0,
                    protein_refs=protein_refs,
                    target_decoy_label=_target_decoy_label_for_refs(protein_refs),
                    contaminant_flag=all(
                        ref.upper().startswith("CON__") for ref in protein_refs
                    ),
                )
            )
    report = build_protein_coverage_report(
        tuple(synthetic_records),
        protein_sequences=protein_sequences,
    )
    return {
        entry.protein_ref: ProteinEvidenceCardCoverage(
            coverage_protein_ref=entry.protein_ref,
            residue_count=entry.residue_count,
            covered_residue_count=entry.covered_residue_count,
            coverage_fraction=entry.coverage_fraction,
            covered_peptides=entry.covered_peptides,
        )
        for entry in report.entries
    }


def _target_decoy_label_for_refs(protein_refs: tuple[str, ...]) -> TargetDecoyLabel:
    normalized_refs = tuple(ref.upper() for ref in protein_refs)
    if normalized_refs and all(
        ref.startswith(("REV__", "DECOY__", "DECOY:")) for ref in normalized_refs
    ):
        return TargetDecoyLabel.DECOY
    return TargetDecoyLabel.TARGET


def _select_representative_protein_ref(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    protein_sequences: dict[str, str],
) -> str:
    annotated_refs = {
        entry.protein_ref
        for entry in annotation_entries
        if entry.annotation_status is ProteinAnnotationStatus.ANNOTATED
    }
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs and protein_ref in protein_sequences:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in annotated_refs:
            return protein_ref
    for protein_ref in protein_refs:
        if protein_ref in protein_sequences:
            return protein_ref
    return protein_refs[0]


def _entry_is_significant(
    entry: DifferentialAbundanceEntry,
    *,
    policy: ProteinEvidenceCardSelectionPolicy,
) -> bool:
    return (
        entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


def _select_context_entries(
    protein_refs: tuple[str, ...],
    *,
    by_protein: dict[str, tuple[ProteinEvidenceCardContextEntry, ...]],
) -> tuple[ProteinEvidenceCardContextEntry, ...]:
    entries = {
        (
            entry.context_kind.value,
            entry.context_id,
            entry.source_accession or "",
        ): entry
        for protein_ref in protein_refs
        for entry in by_protein.get(protein_ref, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.context_kind.value, entry.context_id),
        )
    )


def _select_pathway_entries(
    protein_refs: tuple[str, ...],
    *,
    annotation_entries: tuple[ProteinAnnotationResultEntry, ...],
    by_member: dict[str, tuple[ProteinEvidenceCardPathwayEntry, ...]],
) -> tuple[ProteinEvidenceCardPathwayEntry, ...]:
    gene_symbols = {
        entry.gene_symbol for entry in annotation_entries if entry.gene_symbol
    }
    entries = {
        (
            entry.entry_kind.value,
            entry.entry_id,
            entry.source_accession or "",
        ): entry
        for member_id in (*protein_refs, *sorted(gene_symbols))
        for entry in by_member.get(member_id, ())
    }
    return tuple(
        sorted(
            entries.values(),
            key=lambda entry: (entry.entry_kind.value, entry.entry_id),
        )
    )


def _build_warnings(
    *,
    annotation: ProteinEvidenceCardAnnotation,
    coverage: ProteinEvidenceCardCoverage,
    differential_entry: DifferentialAbundanceEntry,
    significant: bool,
    unique_peptide_count: int,
    peptide_count: int,
) -> tuple[ProteinEvidenceCardWarning, ...]:
    warnings: list[ProteinEvidenceCardWarning] = []
    if not significant:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.NOT_SIGNIFICANT,
                message="final protein result did not satisfy the configured biological selection policy",
            )
        )
    if annotation.annotation_status is ProteinAnnotationStatus.UNMAPPED:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.ANNOTATION_UNMAPPED,
                message="representative protein could not be annotated from the provided FASTA or custom annotation inputs",
            )
        )
    if peptide_count > 0 and unique_peptide_count == 0:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.SHARED_PEPTIDE_ONLY,
                message="protein result is supported only by peptides shared across multiple protein targets",
            )
        )
    elif unique_peptide_count < 2:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.LOW_UNIQUE_PEPTIDE_SUPPORT,
                message="protein result has fewer than two unique member peptides",
            )
        )
    if coverage.residue_count == 0 or coverage.coverage_fraction < 0.1:
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.LOW_SEQUENCE_COVERAGE,
                message="sequence-backed protein coverage remained below 10 percent",
            )
        )
    if (
        differential_entry.not_observed_values_a > 0
        or differential_entry.not_observed_values_b > 0
        or differential_entry.filtered_values_a > 0
        or differential_entry.filtered_values_b > 0
    ):
        warnings.append(
            ProteinEvidenceCardWarning(
                code=ProteinEvidenceCardWarningCode.CONDITION_MISSINGNESS,
                message="differential comparison includes missing or filtered values in at least one condition",
            )
        )
    return tuple(warnings)


def _graph_evidence_tier(
    evidence_tier: FinalClaimEvidenceTier,
) -> ProteinEvidenceCardTier:
    if evidence_tier is FinalClaimEvidenceTier.HIGH_CONFIDENCE:
        return ProteinEvidenceCardTier.HIGH_SUPPORT
    if evidence_tier is FinalClaimEvidenceTier.MODERATE:
        return ProteinEvidenceCardTier.MODERATE_SUPPORT
    return ProteinEvidenceCardTier.REVIEW


def _graph_support_node_ids(report: ProteinEvidenceSummaryReport) -> tuple[str, ...]:
    node_ids = {
        report.protein.node_id,
        *(node.node_id for node in report.mapped_peptides),
        *(node.node_id for node in report.quantifying_peptides),
        *(node.node_id for node in report.protein_groups),
        *(node.node_id for node in report.quant_values),
    }
    return tuple(sorted(node_ids))


def _build_card_id(entity_id: str) -> str:
    return build_protein_card_id(entity_id)


def _build_standard_card_entry(card: ProteinEvidenceCard) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=card.card_id,
        card_kind=StandardCardKind.PROTEIN,
        subject_kind=StandardCardSubjectKind.PROTEIN,
        subject_id=card.representative_protein_ref,
        subject_label=card.annotation.gene_symbol or card.representative_protein_ref,
        claim=(
            f"Protein {card.representative_protein_ref} has log2 fold change "
            f"{card.differential_result.log2_fold_change:g} between "
            f"{card.differential_result.condition_a} and {card.differential_result.condition_b}."
        ),
        evidence_for=(
            f"{card.unique_peptide_count} unique peptides and "
            f"{card.coverage.coverage_fraction:.0%} sequence coverage support this protein."
        ),
        evidence_against=(
            "no explicit weakening evidence was preserved on this protein card."
            if not card.warnings
            else "warnings remained attached: "
            + ", ".join(warning.code.value for warning in card.warnings)
            + "."
        ),
        confidence=_standard_card_confidence(card.evidence_tier),
        warning_codes=tuple(warning.code.value for warning in card.warnings),
        source_ids=card.graph_source_row_refs,
    )


def _standard_card_confidence(tier: ProteinEvidenceCardTier) -> ConfidenceTier:
    if tier is ProteinEvidenceCardTier.HIGH_SUPPORT:
        return ConfidenceTier.HIGH
    if tier is ProteinEvidenceCardTier.MODERATE_SUPPORT:
        return ConfidenceTier.MODERATE
    return ConfidenceTier.LOW


__all__ = [
    "ProteinEvidenceCard",
    "ProteinEvidenceCardAnnotation",
    "ProteinEvidenceCardContextEntry",
    "ProteinEvidenceCardCoverage",
    "ProteinEvidenceCardDifferentialResult",
    "ProteinEvidenceCardPathwayEntry",
    "ProteinEvidenceCardPathwayEntryKind",
    "ProteinEvidenceCardQuantification",
    "ProteinEvidenceCardReport",
    "ProteinEvidenceCardSampleValue",
    "ProteinEvidenceCardSelectionPolicy",
    "ProteinEvidenceCardSummary",
    "ProteinEvidenceCardTier",
    "ProteinEvidenceCardWarning",
    "ProteinEvidenceCardWarningCode",
    "build_protein_evidence_card_report",
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
]
