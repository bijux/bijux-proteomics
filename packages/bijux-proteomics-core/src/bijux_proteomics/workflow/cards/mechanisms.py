# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Mechanism-card workflow over governed biological result surfaces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.domain.semantic_ids import build_mechanism_card_id
from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.interpretation.complex_activity import (
    ComplexActivityConfidenceStatus,
)
from bijux_proteomics.interpretation.pathway_activity import (
    PathwayActivityConfidenceStatus,
)
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceType,
    RegulatorInferenceDirection,
)
from bijux_proteomics.review.belief.biomarker_candidate_ranking import (
    BiomarkerCandidateKind,
    BiomarkerCandidateRankingInput,
    build_biomarker_candidate_ranking_report,
)
from bijux_proteomics.review.evidence_graph.evidence_graph_confidence import (
    EvidenceGraphConfidenceTier,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import ProteinMechanismCard
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results import ProteomicsStudyResult
from bijux_proteomics_foundation import JsonModel


class MechanismCardKind(StrEnum):
    """Stable mechanism-card classes emitted by the workflow surface."""

    PATHWAY_SHIFT = "pathway_shift"
    KINASE_CANDIDATE = "kinase_candidate"
    COMPLEX_CHANGE = "complex_change"
    COMPARTMENT_SIGNAL = "compartment_signal"
    BIOMARKER_CANDIDATE = "biomarker_candidate"


MechanismCardConfidence = ConfidenceTier


class MechanismCard(JsonModel):
    """One integrated mechanism card over governed workflow evidence."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    mechanism_kind: MechanismCardKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    confidence: MechanismCardConfidence
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_surface: str = Field(..., min_length=1)
    source_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    derived_no_source_reason: str | None = None
    evidence_for: tuple[str, ...] = Field(default_factory=tuple)
    evidence_against: tuple[str, ...] = Field(default_factory=tuple)
    missing_evidence: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_source_row_lineage(self) -> MechanismCard:
        SourceRowLineage(
            source_row_refs=self.source_row_refs,
            derived_no_source_reason=self.derived_no_source_reason,
        )
        return self


class MechanismCardSummary(JsonModel):
    """Summary over one integrated mechanism-card workflow pass."""

    model_config = ConfigDict(extra="forbid")

    card_count: int = Field(..., ge=0)
    pathway_shift_count: int = Field(..., ge=0)
    kinase_candidate_count: int = Field(..., ge=0)
    complex_change_count: int = Field(..., ge=0)
    compartment_signal_count: int = Field(..., ge=0)
    biomarker_candidate_count: int = Field(..., ge=0)
    high_confidence_count: int = Field(..., ge=0)
    moderate_confidence_count: int = Field(..., ge=0)
    low_confidence_count: int = Field(..., ge=0)


class MechanismCardReport(JsonModel):
    """Integrated mechanism-card report over one biological result."""

    model_config = ConfigDict(extra="forbid")

    cards: tuple[MechanismCard, ...] = Field(default_factory=tuple)
    summary: MechanismCardSummary
    note: str = Field(..., min_length=1)


def build_mechanism_cards(
    result: ProteomicsStudyResult | BiologicalResultReportBundle,
) -> MechanismCardReport:
    """Build integrated mechanism cards from governed biological result surfaces."""

    report = _biological_report(result)
    cards = tuple(
        sorted(
            (
                *_build_pathway_shift_cards(report),
                *_build_kinase_candidate_cards(report),
                *_build_complex_change_cards(report),
                *_build_compartment_signal_cards(report),
                *_build_biomarker_candidate_cards(report),
            ),
            key=lambda entry: (
                entry.mechanism_kind.value,
                entry.subject_id,
                entry.card_id,
            ),
        )
    )
    return MechanismCardReport(
        cards=cards,
        summary=MechanismCardSummary(
            card_count=len(cards),
            pathway_shift_count=sum(
                card.mechanism_kind is MechanismCardKind.PATHWAY_SHIFT for card in cards
            ),
            kinase_candidate_count=sum(
                card.mechanism_kind is MechanismCardKind.KINASE_CANDIDATE
                for card in cards
            ),
            complex_change_count=sum(
                card.mechanism_kind is MechanismCardKind.COMPLEX_CHANGE
                for card in cards
            ),
            compartment_signal_count=sum(
                card.mechanism_kind is MechanismCardKind.COMPARTMENT_SIGNAL
                for card in cards
            ),
            biomarker_candidate_count=sum(
                card.mechanism_kind is MechanismCardKind.BIOMARKER_CANDIDATE
                for card in cards
            ),
            high_confidence_count=sum(
                card.confidence is MechanismCardConfidence.HIGH for card in cards
            ),
            moderate_confidence_count=sum(
                card.confidence is MechanismCardConfidence.MODERATE for card in cards
            ),
            low_confidence_count=sum(
                card.confidence is MechanismCardConfidence.LOW for card in cards
            ),
        ),
        note=(
            "mechanism cards consolidate governed pathway, kinase, complex, "
            "compartment, and biomarker signals while preserving support, "
            "counterpoints, confidence, and missing evidence explicitly"
        ),
    )


def render_mechanism_card_summary_tsv(report: MechanismCardReport) -> str:
    """Render the integrated mechanism-card summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_count",
            "pathway_shift_count",
            "kinase_candidate_count",
            "complex_change_count",
            "compartment_signal_count",
            "biomarker_candidate_count",
            "high_confidence_count",
            "moderate_confidence_count",
            "low_confidence_count",
        )
    )
    writer.writerow(
        (
            report.summary.card_count,
            report.summary.pathway_shift_count,
            report.summary.kinase_candidate_count,
            report.summary.complex_change_count,
            report.summary.compartment_signal_count,
            report.summary.biomarker_candidate_count,
            report.summary.high_confidence_count,
            report.summary.moderate_confidence_count,
            report.summary.low_confidence_count,
        )
    )
    return buffer.getvalue()


def render_mechanism_cards_tsv(report: MechanismCardReport) -> str:
    """Render integrated mechanism cards as a flat TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "card_id",
            "mechanism_kind",
            "subject_id",
            "subject_label",
            "confidence",
            "confidence_score",
            "source_surface",
            "source_ids",
            "source_row_refs",
            "derived_no_source_reason",
            "evidence_for",
            "evidence_against",
            "missing_evidence",
            "note",
        )
    )
    for card in report.cards:
        writer.writerow(
            (
                card.card_id,
                card.mechanism_kind.value,
                card.subject_id,
                card.subject_label,
                card.confidence.value,
                f"{card.confidence_score:.3f}",
                card.source_surface,
                "|".join(card.source_ids),
                "|".join(card.source_row_refs),
                ""
                if card.derived_no_source_reason is None
                else card.derived_no_source_reason,
                "|".join(card.evidence_for),
                "|".join(card.evidence_against),
                "|".join(card.missing_evidence),
                card.note,
            )
        )
    return buffer.getvalue()


def _biological_report(
    result: ProteomicsStudyResult | BiologicalResultReportBundle,
) -> BiologicalResultReportBundle:
    if isinstance(result, BiologicalResultReportBundle):
        return result
    if result.biological_report is None:
        raise ValueError(
            "mechanism cards require a study result with a governed biological report bundle"
        )
    return result.biological_report


def _build_pathway_shift_cards(
    report: BiologicalResultReportBundle,
) -> tuple[MechanismCard, ...]:
    pathway_report = report.pathway_activity_report
    if pathway_report is None:
        return ()
    unresolved_by_pathway: dict[str, list[str]] = {}
    for entry in pathway_report.unresolved_members:
        unresolved_by_pathway.setdefault(entry.pathway_id, []).append(entry.member_id)
    cards: list[MechanismCard] = []
    enrichment_by_pathway = {}
    if report.pathway_enrichment_report is not None:
        enrichment_by_pathway = {
            entry.pathway_id: entry
            for entry in report.pathway_enrichment_report.entries
        }
    for entry in pathway_report.condition_comparisons:
        evidence_for = [
            (
                "pathway activity delta "
                f"{_format_float(entry.activity_score_delta)} for {entry.condition_b} versus {entry.condition_a}"
            ),
            (f"comparison confidence {entry.comparison_confidence_status.value}"),
        ]
        enrichment = enrichment_by_pathway.get(entry.pathway_id)
        if enrichment is not None:
            evidence_for.append(
                "pathway enrichment ratio "
                f"{_format_float(enrichment.enrichment_ratio)} with overlap {enrichment.foreground_overlap_count}/{enrichment.background_member_count}"
            )
        evidence_against = []
        if (
            entry.comparison_confidence_status
            is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            evidence_against.append(
                "pathway activity comparison remained low confidence"
            )
        unresolved = tuple(sorted(unresolved_by_pathway.get(entry.pathway_id, ())))
        if unresolved:
            evidence_against.append(
                "unresolved pathway members: " + ", ".join(unresolved)
            )
        if not evidence_against:
            evidence_against.append(
                "no direct pathway-level contradiction was preserved"
            )
        missing_evidence = []
        if enrichment is None:
            missing_evidence.append("pathway enrichment companion evidence")
        if unresolved:
            missing_evidence.append("complete pathway member mapping")
        if (
            entry.comparison_confidence_status
            is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            missing_evidence.append(
                "additional high-confidence quantified pathway members"
            )
        if not missing_evidence:
            missing_evidence.append("independent perturbation validation")
        confidence_score = 0.85
        if enrichment is None:
            confidence_score -= 0.15
        if unresolved:
            confidence_score -= 0.15
        if (
            entry.comparison_confidence_status
            is PathwayActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            confidence_score -= 0.25
        cards.append(
            MechanismCard(
                card_id=build_mechanism_card_id(
                    MechanismCardKind.PATHWAY_SHIFT,
                    entry.pathway_id,
                ),
                mechanism_kind=MechanismCardKind.PATHWAY_SHIFT,
                subject_id=entry.pathway_id,
                subject_label=entry.pathway_name or entry.pathway_id,
                confidence=_confidence_from_score(confidence_score),
                confidence_score=_clamp_score(confidence_score),
                source_surface="pathway_activity_report",
                source_ids=(entry.pathway_id,),
                derived_no_source_reason=_derived_no_source_reason(
                    "pathway activity comparisons aggregate governed member-contribution and condition-score surfaces rather than one direct input row"
                ),
                evidence_for=tuple(evidence_for),
                evidence_against=tuple(evidence_against),
                missing_evidence=tuple(missing_evidence),
                note=(
                    "pathway shift cards preserve pathway-level condition deltas and "
                    "do not hide unresolved members or missing enrichment support"
                ),
            )
        )
    return tuple(cards)


def _build_kinase_candidate_cards(
    report: BiologicalResultReportBundle,
) -> tuple[MechanismCard, ...]:
    regulator_report = report.regulator_inference_report
    if regulator_report is None:
        return ()
    unresolved_by_regulator: dict[str, list[str]] = {}
    for entry in regulator_report.unresolved_targets:
        unresolved_by_regulator.setdefault(entry.regulator, []).append(
            entry.target_value
        )
    cards: list[MechanismCard] = []
    for entry in regulator_report.entries:
        if entry.evidence_type is not RegulatorEvidenceType.KINASE_SUBSTRATE:
            continue
        evidence_for = [
            (
                f"kinase score {_format_float(entry.score)} with coverage "
                f"{_format_float(entry.coverage_fraction)}"
            ),
            (
                "supporting site keys: "
                + (
                    ", ".join(entry.supporting_site_keys)
                    if entry.supporting_site_keys
                    else "none preserved"
                )
            ),
        ]
        evidence_against = []
        if entry.direction is RegulatorInferenceDirection.UNSUPPORTED:
            evidence_against.append("observed regulator direction remained unsupported")
        unresolved = tuple(sorted(unresolved_by_regulator.get(entry.regulator, ())))
        if unresolved:
            evidence_against.append(
                "unresolved regulator targets: " + ", ".join(unresolved)
            )
        if not evidence_against:
            evidence_against.append(
                "no direct kinase-level contradiction was preserved"
            )
        missing_evidence = []
        if not entry.supporting_site_keys:
            missing_evidence.append("site-level substrate regulation support")
        if entry.coverage_fraction < 1.0:
            missing_evidence.append("complete kinase target coverage")
        if not missing_evidence:
            missing_evidence.append("orthogonal kinase perturbation evidence")
        confidence_score = entry.score
        if entry.direction is RegulatorInferenceDirection.UNSUPPORTED:
            confidence_score -= 0.25
        if unresolved:
            confidence_score -= 0.15
        cards.append(
            MechanismCard(
                card_id=build_mechanism_card_id(
                    MechanismCardKind.KINASE_CANDIDATE,
                    entry.regulator,
                ),
                mechanism_kind=MechanismCardKind.KINASE_CANDIDATE,
                subject_id=entry.regulator,
                subject_label=entry.regulator,
                confidence=_confidence_from_score(confidence_score),
                confidence_score=_clamp_score(confidence_score),
                source_surface="regulator_inference_report",
                source_ids=(entry.regulator, *entry.supporting_site_keys),
                derived_no_source_reason=_derived_no_source_reason(
                    "regulator inference cards aggregate governed upstream-target evidence and downstream signal surfaces rather than one direct input row"
                ),
                evidence_for=tuple(evidence_for),
                evidence_against=tuple(evidence_against),
                missing_evidence=tuple(missing_evidence),
                note=(
                    "kinase candidate cards preserve explicit kinase-substrate support "
                    "and keep unresolved or unsupported regulator evidence visible"
                ),
            )
        )
    return tuple(cards)


def _build_complex_change_cards(
    report: BiologicalResultReportBundle,
) -> tuple[MechanismCard, ...]:
    complex_report = report.complex_activity_report
    if complex_report is None:
        return ()
    unresolved_by_complex: dict[str, list[str]] = {}
    for entry in complex_report.unresolved_members:
        unresolved_by_complex.setdefault(entry.complex_id, []).append(entry.member_id)
    cards: list[MechanismCard] = []
    for entry in complex_report.condition_comparisons:
        evidence_for = [
            (
                "complex activity delta "
                f"{_format_float(entry.activity_score_delta)} for {entry.condition_b} versus {entry.condition_a}"
            ),
            (f"comparison confidence {entry.comparison_confidence_status.value}"),
        ]
        evidence_against = []
        limiting_members = tuple(
            sorted(
                {
                    *entry.condition_a_limiting_member_ids,
                    *entry.condition_b_limiting_member_ids,
                }
            )
        )
        if limiting_members:
            evidence_against.append(
                "limiting complex members: " + ", ".join(limiting_members)
            )
        if (
            entry.comparison_confidence_status
            is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            evidence_against.append(
                "complex activity comparison remained low confidence"
            )
        unresolved = tuple(sorted(unresolved_by_complex.get(entry.complex_id, ())))
        if unresolved:
            evidence_against.append(
                "unresolved complex members: " + ", ".join(unresolved)
            )
        if not evidence_against:
            evidence_against.append(
                "no direct complex-level contradiction was preserved"
            )
        missing_evidence = []
        if limiting_members:
            missing_evidence.append("balanced quantification for limiting subunits")
        if unresolved:
            missing_evidence.append("complete complex member mapping")
        if (
            entry.comparison_confidence_status
            is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            missing_evidence.append("additional observed complex members")
        if not missing_evidence:
            missing_evidence.append("orthogonal complex assembly evidence")
        confidence_score = 0.85
        if limiting_members:
            confidence_score -= 0.15
        if unresolved:
            confidence_score -= 0.15
        if (
            entry.comparison_confidence_status
            is ComplexActivityConfidenceStatus.LOW_CONFIDENCE
        ):
            confidence_score -= 0.25
        cards.append(
            MechanismCard(
                card_id=build_mechanism_card_id(
                    MechanismCardKind.COMPLEX_CHANGE,
                    entry.complex_id,
                ),
                mechanism_kind=MechanismCardKind.COMPLEX_CHANGE,
                subject_id=entry.complex_id,
                subject_label=entry.complex_name or entry.complex_id,
                confidence=_confidence_from_score(confidence_score),
                confidence_score=_clamp_score(confidence_score),
                source_surface="complex_activity_report",
                source_ids=(entry.complex_id,),
                derived_no_source_reason=_derived_no_source_reason(
                    "complex activity cards aggregate governed complex-member and condition-comparison surfaces rather than one direct input row"
                ),
                evidence_for=tuple(evidence_for),
                evidence_against=tuple(evidence_against),
                missing_evidence=tuple(missing_evidence),
                note=(
                    "complex change cards preserve limiting or unresolved members "
                    "instead of overstating complete assembly support"
                ),
            )
        )
    return tuple(cards)


def _build_compartment_signal_cards(
    report: BiologicalResultReportBundle,
) -> tuple[MechanismCard, ...]:
    compartment_report = report.compartment_biology_report
    if compartment_report is None:
        return ()
    enrichment_by_set = {
        entry.set_id: entry for entry in compartment_report.enrichment_report.entries
    }
    unknown_foreground = tuple(
        sorted(
            entry.protein_ref
            for entry in compartment_report.unknown_localization_entries
            if entry.localization_scope.value == "foreground"
        )
    )
    cards: list[MechanismCard] = []
    for entry in compartment_report.activity_report.condition_comparisons:
        enrichment = enrichment_by_set.get(entry.set_id)
        evidence_for = [
            (
                "compartment activity delta "
                f"{_format_float(entry.activity_score_delta)} for {entry.condition_b} versus {entry.condition_a}"
            ),
            (f"comparison confidence {entry.comparison_confidence_status.value}"),
        ]
        if enrichment is not None:
            evidence_for.append(
                "compartment enrichment ratio "
                f"{_format_float(enrichment.enrichment_ratio)} with overlap {enrichment.foreground_overlap_count}/{enrichment.background_member_count}"
            )
        evidence_against = []
        if entry.comparison_confidence_status.value == "low":
            evidence_against.append(
                "compartment activity comparison remained low confidence"
            )
        if unknown_foreground:
            evidence_against.append(
                "foreground proteins without compartment mapping: "
                + ", ".join(unknown_foreground)
            )
        if not evidence_against:
            evidence_against.append(
                "no direct compartment-level contradiction was preserved"
            )
        missing_evidence = []
        if enrichment is None:
            missing_evidence.append("compartment enrichment companion evidence")
        if unknown_foreground:
            missing_evidence.append("complete foreground compartment annotation")
        if entry.comparison_confidence_status.value == "low":
            missing_evidence.append(
                "additional localized proteins with high-confidence scores"
            )
        if not missing_evidence:
            missing_evidence.append("orthogonal localization validation")
        confidence_score = 0.8
        if enrichment is None:
            confidence_score -= 0.15
        if unknown_foreground:
            confidence_score -= 0.15
        if entry.comparison_confidence_status.value == "low":
            confidence_score -= 0.25
        cards.append(
            MechanismCard(
                card_id=build_mechanism_card_id(
                    MechanismCardKind.COMPARTMENT_SIGNAL,
                    entry.set_id,
                ),
                mechanism_kind=MechanismCardKind.COMPARTMENT_SIGNAL,
                subject_id=entry.set_id,
                subject_label=entry.set_name or entry.set_id,
                confidence=_confidence_from_score(confidence_score),
                confidence_score=_clamp_score(confidence_score),
                source_surface="compartment_biology_report",
                source_ids=(entry.set_id,),
                derived_no_source_reason=_derived_no_source_reason(
                    "compartment signal cards aggregate governed localization, enrichment, and activity surfaces rather than one direct input row"
                ),
                evidence_for=tuple(evidence_for),
                evidence_against=tuple(evidence_against),
                missing_evidence=tuple(missing_evidence),
                note=(
                    "compartment signal cards keep unknown localization gaps explicit "
                    "instead of treating compartment labels as complete"
                ),
            )
        )
    return tuple(cards)


def _build_biomarker_candidate_cards(
    report: BiologicalResultReportBundle,
) -> tuple[MechanismCard, ...]:
    candidates = tuple(
        _biomarker_candidate_from_mechanism_card(card, report)
        for card in report.protein_mechanism_cards.cards
        if card.abundance_change.significant
    )
    if not candidates:
        return ()
    ranking = build_biomarker_candidate_ranking_report(candidates)
    mechanism_cards_by_id = {
        card.card_id: card for card in report.protein_mechanism_cards.cards
    }
    cards: list[MechanismCard] = []
    for entry in ranking.entries:
        source_card = mechanism_cards_by_id[entry.candidate_id]
        evidence_for = [
            (
                "ranked biomarker priority "
                f"{entry.priority_rank} with trust score {entry.decomposition.final_score:.3f}"
            ),
            (
                "effect size "
                f"{_format_float(entry.effect_size)} supported by {entry.support_count} evidence row(s)"
            ),
        ]
        evidence_against = []
        if entry.decomposition.penalty_total > 0.0:
            evidence_against.append(
                f"ranking penalties totaled {entry.decomposition.penalty_total:.3f}"
            )
        if source_card.warning_codes:
            evidence_against.append(
                "protein evidence warnings: "
                + ", ".join(code.value for code in source_card.warning_codes)
            )
        if not evidence_against:
            evidence_against.append(
                "no direct biomarker-level contradiction was preserved"
            )
        missing_evidence = []
        if entry.decomposition.uncertainty > 0.0:
            missing_evidence.append(
                f"uncertainty reduction for score discount {entry.decomposition.uncertainty:.3f}"
            )
        if source_card.peptide_support.unique_peptide_count < 2:
            missing_evidence.append("additional unique peptide support")
        if not missing_evidence:
            missing_evidence.append("targeted validation assay confirmation")
        cards.append(
            MechanismCard(
                card_id=build_mechanism_card_id(
                    MechanismCardKind.BIOMARKER_CANDIDATE,
                    entry.candidate_id,
                ),
                mechanism_kind=MechanismCardKind.BIOMARKER_CANDIDATE,
                subject_id=entry.candidate_id,
                subject_label=entry.display_label,
                confidence=_confidence_from_score(entry.decomposition.final_score),
                confidence_score=entry.decomposition.final_score,
                source_surface="protein_mechanism_cards",
                source_ids=tuple(sorted({entry.candidate_id, *entry.source_ids})),
                source_row_refs=source_card.source_row_refs,
                derived_no_source_reason=source_card.derived_no_source_reason,
                evidence_for=tuple(evidence_for),
                evidence_against=tuple(evidence_against),
                missing_evidence=tuple(missing_evidence),
                note=(
                    "biomarker candidate cards preserve ranking penalties and "
                    "uncertainty instead of promoting all significant proteins equally"
                ),
            )
        )
    return tuple(cards)


def _biomarker_candidate_from_mechanism_card(
    card: ProteinMechanismCard,
    report: BiologicalResultReportBundle,
) -> BiomarkerCandidateRankingInput:
    effect_score = min(1.0, abs(card.abundance_change.log2_fold_change) / 3.0)
    robustness_score = {
        EvidenceGraphConfidenceTier.HIGH: 0.9,
        EvidenceGraphConfidenceTier.MODERATE: 0.7,
        EvidenceGraphConfidenceTier.LOW: 0.45,
    }[card.confidence_tier]
    detectability_score = min(
        1.0,
        0.5 * card.peptide_support.coverage_fraction
        + 0.1 * min(card.peptide_support.unique_peptide_count, 5),
    )
    specificity_score = max(
        0.0,
        min(
            1.0,
            0.8 if card.peptide_support.shared_peptide_count == 0 else 0.45,
        ),
    )
    annotation_score = min(
        1.0,
        0.2 * bool(card.pathways)
        + 0.2 * bool(card.complexes)
        + 0.2 * bool(card.domains)
        + 0.2 * bool(card.ptms)
        + 0.2 * bool(card.gene_symbol),
    )
    assay_feasibility_score = min(
        1.0,
        0.3
        + 0.2 * min(card.peptide_support.unique_peptide_count, 3)
        - 0.1 * len(card.warning_codes),
    )
    sample_qc_score = report.experiment_confidence_report.summary.overall_score
    annotation_labels = tuple(
        sorted(
            {
                *(entry.entry_name or entry.entry_id for entry in card.pathways),
                *(entry.entry_name or entry.entry_id for entry in card.complexes),
            }
        )
    )
    return BiomarkerCandidateRankingInput(
        candidate_id=card.card_id,
        candidate_kind=BiomarkerCandidateKind.PROTEIN,
        display_label=card.gene_symbol or card.representative_protein_ref,
        target_protein_ref=card.representative_protein_ref,
        effect_size=card.abundance_change.log2_fold_change,
        adjusted_p_value=card.abundance_change.adjusted_p_value,
        support_count=max(1, card.peptide_support.graph_support_edge_count),
        effect_score=effect_score,
        robustness_score=robustness_score,
        detectability_score=_clamp_score(detectability_score),
        specificity_score=specificity_score,
        annotation_score=annotation_score,
        assay_feasibility_score=_clamp_score(assay_feasibility_score),
        sample_qc_score=sample_qc_score,
        annotation_labels=annotation_labels,
        source_ids=(card.card_id, card.graph_claim_node_id, card.protein_card_id),
        uncertainty=min(
            1.0, 0.1 * len(card.warning_codes) + 0.05 * len(card.downgrade_reasons)
        ),
        note="protein mechanism card promoted into biomarker candidate ranking input",
    )


def _confidence_from_score(score: float) -> MechanismCardConfidence:
    if score >= 0.75:
        return MechanismCardConfidence.HIGH
    if score >= 0.5:
        return MechanismCardConfidence.MODERATE
    return MechanismCardConfidence.LOW


def _clamp_score(score: float) -> float:
    return round(max(0.0, min(1.0, score)), 6)


def _format_float(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def _derived_no_source_reason(reason: str) -> str:
    return (
        SourceRowLineage.from_derived_reason(reason).derived_no_source_reason or reason
    )


__all__ = [
    "MechanismCard",
    "MechanismCardConfidence",
    "MechanismCardKind",
    "MechanismCardReport",
    "MechanismCardSummary",
    "build_mechanism_cards",
    "render_mechanism_card_summary_tsv",
    "render_mechanism_cards_tsv",
]
