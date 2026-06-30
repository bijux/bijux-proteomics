# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Study-result models and archive queries owned by the study-result surface."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.errors import (
    InvalidWorkflowError,
    ScientificEvidenceError,
)
from bijux_proteomics.lab import LabActionPacket
from bijux_proteomics.ptm import PtmReportBundle
from bijux_proteomics.review.evidence_graph import ProteomicsEvidenceGraph
from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultPathway,
    InteractiveResultPeptide,
    InteractiveResultProtein,
    InteractiveResultPtmSite,
)
from bijux_proteomics.workflow.exports.result_manifest import ResultManifestReport
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics_foundation import JsonModel


class ProteomicsStudyKind(StrEnum):
    """Durable study classes normalized onto one comparison surface."""

    ARCHIVED = "archived"
    LABEL_FREE = "label_free"
    DDA = "dda"
    DIA = "dia"
    MAXQUANT = "maxquant"
    TMT = "tmt"
    PTM = "ptm"
    TARGETED = "targeted"


class ProteomicsStudyMatrixKind(StrEnum):
    """Stable matrix surfaces preserved on a study result."""

    HEATMAP_REVIEW = "heatmap_review"
    LABEL_FREE_PROTEIN = "label_free_protein"
    DIA_PRECURSOR = "dia_precursor"
    DIA_PEPTIDE = "dia_peptide"
    DIA_PROTEIN = "dia_protein"
    REPORTER_CHANNEL = "reporter_channel"
    PROTEIN_RATIO = "protein_ratio"
    PTM_SITE = "ptm_site"
    TARGETED_TARGET = "targeted_target"


class ProteomicsStudyStatisticKind(StrEnum):
    """Stable quantitative-result surfaces preserved on a study result."""

    DIFFERENTIAL_PROTEIN = "differential_protein"
    DIFFERENTIAL_LABEL_BASED = "differential_label_based"
    DIFFERENTIAL_PTM_SITE = "differential_ptm_site"
    TARGETED_VALIDATION = "targeted_validation"


class ProteomicsStudyQcKind(StrEnum):
    """Stable QC and acceptance surfaces preserved on a study result."""

    ARCHIVED_RESULT = "archived_result"
    SAMPLE_EXPLORATION = "sample_exploration"
    EXPERIMENT_CONFIDENCE = "experiment_confidence"
    DDA_ACCEPTANCE = "dda_acceptance"
    DDA_PARSIMONY = "dda_parsimony"
    DIA_RUN_QC = "dia_run_qc"
    MAXQUANT_IMPORT = "maxquant_import"
    MAXQUANT_ACCEPTANCE = "maxquant_acceptance"
    TMT_METADATA_VALIDATION = "tmt_metadata_validation"
    LABEL_BASED_SAMPLE_QC = "label_based_sample_qc"
    PTM_EVIDENCE_PARSING = "ptm_evidence_parsing"
    LAB_ACTION_PACKET = "lab_action_packet"
    BELIEF_AUDIT = "belief_audit"
    FRAGMENT_COHERENCE = "fragment_coherence"
    PROTEIN_GROUP_DISCREPANCY = "protein_group_discrepancy"
    PTM_AMBIGUITY_REVIEW = "ptm_ambiguity_review"
    LABEL_BASED_SIGNAL_REVIEW = "label_based_signal_review"
    TARGETED_ASSAY_QC = "targeted_assay_qc"


class ProteomicsStudyCardKind(StrEnum):
    """Stable evidence-card surfaces preserved on a study result."""

    PROTEIN_EVIDENCE = "protein_evidence"
    PROTEIN_MECHANISM = "protein_mechanism"
    PTM_EVIDENCE = "ptm_evidence"
    TARGETED_VALIDATION = "targeted_validation"


class ProteomicsStudyConclusionKind(StrEnum):
    """Stable biological conclusion surfaces comparable across study results."""

    SUPPORTED_CLAIM = "supported_claim"
    REFUSED_CLAIM = "refused_claim"
    REJECTED_CLAIM = "rejected_claim"
    BIOLOGICAL_HYPOTHESIS = "biological_hypothesis"
    REGULATOR_INFERENCE = "regulator_inference"
    PTM_NARRATIVE_CLAIM = "ptm_narrative_claim"


class ProteomicsStudyDesignEntry(JsonModel):
    """One sample-level design row normalized for cross-study comparison."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    replicate: str | None = None
    fraction: str | None = None
    batch: str | None = None
    pair_id: str | None = None
    multiplex_group: str | None = None
    multiplex_channel: str | None = None
    sample_role: str | None = None


class ProteomicsStudyDesignSnapshot(JsonModel):
    """Programmatic design snapshot carried by one study result."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteomicsStudyDesignEntry, ...] = Field(default_factory=tuple)
    sample_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    batch_count: int = Field(..., ge=0)
    paired_sample_count: int = Field(..., ge=0)
    multiplexed_sample_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteomicsStudyMatrixSurface(JsonModel):
    """One matrix-like surface preserved on a study result."""

    model_config = ConfigDict(extra="forbid")

    surface_name: str = Field(..., min_length=1)
    kind: ProteomicsStudyMatrixKind
    entity_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteomicsStudyStatisticSurface(JsonModel):
    """One statistical result surface preserved on a study result."""

    model_config = ConfigDict(extra="forbid")

    surface_name: str = Field(..., min_length=1)
    kind: ProteomicsStudyStatisticKind
    entity_count: int = Field(..., ge=0)
    significant_entity_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteomicsStudyQcSurface(JsonModel):
    """One QC or acceptance surface preserved on a study result."""

    model_config = ConfigDict(extra="forbid")

    surface_name: str = Field(..., min_length=1)
    kind: ProteomicsStudyQcKind
    issue_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteomicsStudyCardSurface(JsonModel):
    """One evidence-card surface preserved on a study result."""

    model_config = ConfigDict(extra="forbid")

    surface_name: str = Field(..., min_length=1)
    kind: ProteomicsStudyCardKind
    card_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteomicsStudyConclusionEntry(JsonModel):
    """One biological conclusion emitted from a governed study result surface."""

    model_config = ConfigDict(extra="forbid")

    conclusion_id: str = Field(..., min_length=1)
    kind: ProteomicsStudyConclusionKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_surface: str = Field(..., min_length=1)
    summary_text: str = Field(..., min_length=1)


class ProteomicsStudyResultSummary(JsonModel):
    """Compact summary over one normalized study-level result object."""

    model_config = ConfigDict(extra="forbid")

    design_entry_count: int = Field(..., ge=0)
    matrix_surface_count: int = Field(..., ge=0)
    statistic_surface_count: int = Field(..., ge=0)
    qc_surface_count: int = Field(..., ge=0)
    card_surface_count: int = Field(..., ge=0)
    conclusion_count: int = Field(..., ge=0)


class ProteomicsStudyResult(JsonModel):
    """Study-level object that allows owned workflow results to be compared directly."""

    model_config = ConfigDict(extra="forbid")

    study_kind: ProteomicsStudyKind
    source_surface: str = Field(..., min_length=1)
    design: ProteomicsStudyDesignSnapshot
    matrix_surfaces: tuple[ProteomicsStudyMatrixSurface, ...] = Field(
        default_factory=tuple
    )
    statistic_surfaces: tuple[ProteomicsStudyStatisticSurface, ...] = Field(
        default_factory=tuple
    )
    qc_surfaces: tuple[ProteomicsStudyQcSurface, ...] = Field(default_factory=tuple)
    card_surfaces: tuple[ProteomicsStudyCardSurface, ...] = Field(default_factory=tuple)
    biological_conclusions: tuple[ProteomicsStudyConclusionEntry, ...] = Field(
        default_factory=tuple
    )
    archived_lab_action_packets: tuple[LabActionPacket, ...] = Field(
        default_factory=tuple
    )
    biological_report: BiologicalResultReportBundle | None = None
    label_based_report: LabelBasedReportBundle | None = None
    ptm_report: PtmReportBundle | None = None
    interactive_result_bundle: InteractiveResultBundle | None = None
    archive_manifest: ResultManifestReport | None = None
    archived_evidence_graph: ProteomicsEvidenceGraph | None = None
    summary: ProteomicsStudyResultSummary
    note: str = Field(..., min_length=1)

    def query_archived_protein(
        self,
        *,
        object_id: str | None = None,
        representative_protein_ref: str | None = None,
    ) -> InteractiveResultProtein:
        """Return one archived protein row without rerunning any workflow surface."""

        bundle = self._require_interactive_result_bundle()
        if object_id is None and representative_protein_ref is None:
            raise ScientificEvidenceError(
                "archived protein query requires object_id or representative_protein_ref"
            )
        for protein in bundle.proteins:
            if object_id is not None and protein.object_id == object_id:
                return protein
            if (
                representative_protein_ref is not None
                and protein.representative_protein_ref == representative_protein_ref
            ):
                return protein
        target = object_id or representative_protein_ref or ""
        raise ScientificEvidenceError(
            f"archived protein is missing from result archive: {target}"
        )

    def query_archived_peptide(
        self,
        *,
        peptide_id: str,
    ) -> InteractiveResultPeptide:
        """Return one archived peptide row without rerunning any workflow surface."""

        bundle = self._require_interactive_result_bundle()
        for peptide in bundle.peptides:
            if peptide.peptide_id == peptide_id:
                return peptide
        raise ScientificEvidenceError(
            f"archived peptide is missing from result archive: {peptide_id}"
        )

    def query_archived_ptm_site(
        self,
        *,
        site_key: str,
    ) -> InteractiveResultPtmSite:
        """Return one archived PTM-site row without rerunning any workflow surface."""

        bundle = self._require_interactive_result_bundle()
        for site in bundle.ptm_sites:
            if site.site_key == site_key:
                return site
        raise ScientificEvidenceError(
            f"archived PTM site is missing from result archive: {site_key}"
        )

    def query_archived_pathway(
        self,
        *,
        pathway_id: str,
    ) -> InteractiveResultPathway:
        """Return one archived pathway row without rerunning any workflow surface."""

        bundle = self._require_interactive_result_bundle()
        for pathway in bundle.pathways:
            if pathway.pathway_id == pathway_id:
                return pathway
        raise ScientificEvidenceError(
            f"archived pathway is missing from result archive: {pathway_id}"
        )

    def query_archived_lab_action_packets(
        self,
        *,
        entity_id: str,
        entity_type: str | None = None,
    ) -> tuple[LabActionPacket, ...]:
        """Return archived lab action packets for one failed run or sample."""

        packets = tuple(
            packet
            for packet in self.archived_lab_action_packets
            if packet.entity_id == entity_id
            and (entity_type is None or packet.entity_type == entity_type)
        )
        if packets:
            return packets
        target = entity_id if entity_type is None else f"{entity_type}:{entity_id}"
        raise ScientificEvidenceError(
            f"archived lab action packet is missing from result archive: {target}"
        )

    def _require_interactive_result_bundle(self) -> InteractiveResultBundle:
        if self.interactive_result_bundle is None:
            raise InvalidWorkflowError(
                "study result does not preserve an interactive archive bundle"
            )
        return self.interactive_result_bundle


__all__ = [
    "ProteomicsStudyCardKind",
    "ProteomicsStudyCardSurface",
    "ProteomicsStudyConclusionEntry",
    "ProteomicsStudyConclusionKind",
    "ProteomicsStudyDesignEntry",
    "ProteomicsStudyDesignSnapshot",
    "ProteomicsStudyKind",
    "ProteomicsStudyMatrixKind",
    "ProteomicsStudyMatrixSurface",
    "ProteomicsStudyQcKind",
    "ProteomicsStudyQcSurface",
    "ProteomicsStudyResult",
    "ProteomicsStudyResultSummary",
    "ProteomicsStudyStatisticKind",
    "ProteomicsStudyStatisticSurface",
]
