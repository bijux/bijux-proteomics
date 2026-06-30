# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein-evidence card models and builder preparation contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.interpretation import (
    BiologicalContextKind,
    ProteinAnnotationStatus,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    MissingValueKind,
)
from bijux_proteomics.review import (
    EvidenceGraphFinalResultEntry,
    ProteinEvidenceSummaryReport,
    ProteomicsEvidenceNodeKind,
)
from bijux_proteomics.sequences.protein_identity_resolution import (
    ProteinIdentityLevel,
)
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
)
from bijux_proteomics.sequences.proteogenomic_peptide_support import (
    ProteogenomicPeptideSupportEntry,
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
    "_PreparedProteinCard",
]
