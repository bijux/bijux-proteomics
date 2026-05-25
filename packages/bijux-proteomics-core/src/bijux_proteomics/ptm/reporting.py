# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned PTM reporting surfaces."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.contracts import (
    PtmEvidenceRecord,
    PtmSiteEntry,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
)
from bijux_proteomics.ptm.differential_analysis import (
    PtmDifferentialAnalysisReport,
    render_ptm_differential_volcano_tsv,
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    render_ptm_site_differential_tsv,
)
from bijux_proteomics.ptm.evidence_cards import (
    PtmEvidenceCardPolicy,
    PtmEvidenceCardReport,
    build_ptm_evidence_card_report,
    render_ptm_evidence_card_tsv,
    render_ptm_evidence_card_summary_tsv,
    render_ptm_evidence_claim_tsv,
)
from bijux_proteomics.ptm.localization_scoring import (
    PtmLocalizationScoringReport,
    build_ptm_localization_scoring_report,
    render_ptm_localization_scoring_entry_tsv,
)
from bijux_proteomics.ptm.mechanism_classification import (
    PtmMechanismClassificationReport,
    build_ptm_mechanism_classification_report,
    render_ptm_mechanism_classification_summary_tsv,
    render_ptm_mechanism_classification_tsv,
)
from bijux_proteomics.ptm.motif_analysis import (
    PtmMotifComparisonPolicy,
    PtmPhosphositeMotifEnrichmentReport,
    PtmPhosphositeSelectionPolicy,
    build_ptm_phosphosite_motif_enrichment_report,
    render_ptm_phosphosite_motif_enriched_term_tsv,
    render_ptm_phosphosite_motif_frequency_tsv,
    render_ptm_phosphosite_motif_logo_tsv,
    render_ptm_phosphosite_motif_window_tsv,
)
from bijux_proteomics.ptm.ortholog_site_conservation import (
    PtmOrthologConservationReport,
    PtmOrthologSiteRecord,
    build_ptm_ortholog_conservation_report,
    render_ptm_ortholog_conservation_summary_tsv,
    render_ptm_ortholog_conservation_tsv,
)
from bijux_proteomics.ptm.regulator_enrichment import (
    PtmRegulatorEnrichmentPolicy,
    PtmRegulatorEnrichmentReport,
    build_ptm_regulator_enrichment_report,
    render_ptm_regulator_enrichment_summary_tsv,
    render_ptm_regulator_enrichment_tsv,
)
from bijux_proteomics.ptm.protein_site_mapping import render_ptm_site_table_tsv
from bijux_proteomics.ptm.site_annotation_import import (
    PtmSiteAnnotationRecord,
    build_ptm_site_annotation_mapping_report,
)
from bijux_proteomics.ptm.ambiguity_handling import (
    render_ptm_site_group_quant_matrix_tsv,
    render_ptm_site_group_quant_missingness_tsv,
    render_ptm_site_group_quant_summary_tsv,
)
from bijux_proteomics.ptm.site_quantification import (
    PtmSiteQuantAmbiguityPolicy,
    PtmSiteQuantificationReport,
    build_ptm_site_quantification_report,
    render_ptm_site_quant_matrix_tsv,
    render_ptm_site_quant_missingness_tsv,
)
from bijux_proteomics.quantification import Ms1FeatureRecord, NormalizationMethod
from bijux_proteomics.review import (
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    EvidenceAwareRankingReport,
    build_evidence_aware_ranking_report,
    normalize_linear_range,
    render_evidence_aware_ranking_tsv,
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.sequences import NormalizedProteinRecord, ProteinRegionContextRecord
from bijux_proteomics_foundation import JsonModel


class PtmReportPeptideEntry(JsonModel):
    """One PTM peptide observation carried into a report bundle."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    localized_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    localization_score: float = Field(..., ge=0.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel


class PtmReportSummary(JsonModel):
    """Compact summary over the current PTM report bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_evidence_count: int = Field(..., ge=0)
    peptide_entry_count: int = Field(..., ge=0)
    site_row_count: int = Field(..., ge=0)
    ambiguous_site_count: int = Field(..., ge=0)
    ambiguous_group_row_count: int = Field(..., ge=0)
    modified_peptide_count: int = Field(..., ge=0)
    localization_entry_count: int = Field(..., ge=0)
    quantified_site_row_count: int = Field(..., ge=0)
    differential_site_count: int = Field(..., ge=0)
    motif_term_count: int = Field(..., ge=0)
    evidence_card_count: int = Field(..., ge=0)
    narrative_claim_count: int = Field(..., ge=0)
    mechanism_classification_count: int = Field(..., ge=0)
    ortholog_conservation_entry_count: int = Field(..., ge=0)


class PtmReportBundle(JsonModel):
    """Owned PTM report bundle over evidence-derived peptide and site surfaces."""

    model_config = ConfigDict(extra="forbid")

    peptide_entries: tuple[PtmReportPeptideEntry, ...] = Field(default_factory=tuple)
    site_table: tuple[PtmSiteEntry, ...] = Field(default_factory=tuple)
    localization_scoring: PtmLocalizationScoringReport
    site_quantification: PtmSiteQuantificationReport | None = None
    differential_analysis: PtmDifferentialAnalysisReport | None = None
    mechanism_classification: PtmMechanismClassificationReport | None = None
    motif_enrichment: PtmPhosphositeMotifEnrichmentReport | None = None
    regulator_enrichment: PtmRegulatorEnrichmentReport | None = None
    ortholog_conservation: PtmOrthologConservationReport | None = None
    evidence_cards: PtmEvidenceCardReport | None = None
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None = None
    summary: PtmReportSummary
    note: str = Field(..., min_length=1)


class PtmReportArtifactPaths(JsonModel):
    """Relative PTM report artifact paths written into one output directory."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    peptide_tsv: str = Field(..., min_length=1)
    site_tsv: str = Field(..., min_length=1)
    localization_tsv: str = Field(..., min_length=1)
    site_quant_matrix_tsv: str | None = None
    site_quant_missingness_tsv: str | None = None
    site_group_summary_tsv: str | None = None
    site_group_matrix_tsv: str | None = None
    site_group_missingness_tsv: str | None = None
    differential_tsv: str | None = None
    differential_volcano_tsv: str | None = None
    motif_window_tsv: str | None = None
    motif_frequency_tsv: str | None = None
    motif_term_tsv: str | None = None
    motif_logo_tsv: str | None = None
    regulator_enrichment_summary_tsv: str | None = None
    regulator_enrichment_tsv: str | None = None
    mechanism_classification_summary_tsv: str | None = None
    mechanism_classification_tsv: str | None = None
    ortholog_conservation_summary_tsv: str | None = None
    ortholog_conservation_tsv: str | None = None
    evidence_card_summary_tsv: str | None = None
    evidence_card_tsv: str | None = None
    evidence_claim_tsv: str | None = None
    evidence_aware_ranking_tsv: str | None = None


class PtmReportExportManifest(JsonModel):
    """Stable PTM report manifest over one exported report directory."""

    model_config = ConfigDict(extra="forbid")

    summary: PtmReportSummary
    artifacts: PtmReportArtifactPaths
    motif_summary_included: bool
    note: str = Field(..., min_length=1)


def build_ptm_report_bundle(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    protein_sequences: dict[str, str],
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None,
    feature_records: tuple[Ms1FeatureRecord, ...] | None = None,
    design_entries: tuple[ExperimentalDesignEntry, ...] | None = None,
    ambiguity_policy: PtmSiteQuantAmbiguityPolicy = PtmSiteQuantAmbiguityPolicy.PRESERVE,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    condition_a: str | None = None,
    condition_b: str | None = None,
    protein_correction_mode: PtmProteinCorrectionMode = PtmProteinCorrectionMode.NONE,
    batch_field: str = "batch",
    covariate_fields: tuple[str, ...] = (),
    pairing_field: str | None = None,
    motif_flank_size: int = 7,
    motif_selection_policy: PtmPhosphositeSelectionPolicy | None = None,
    motif_comparison_policy: PtmMotifComparisonPolicy | None = None,
    annotation_records: tuple[PtmSiteAnnotationRecord, ...] | None = None,
    annotation_target_species: str | None = None,
    regulator_enrichment_policy: PtmRegulatorEnrichmentPolicy | None = None,
    ortholog_site_records: tuple[PtmOrthologSiteRecord, ...] | None = None,
    ortholog_source_species: str | None = None,
    ortholog_target_species: str | None = None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...] | None = None,
    evidence_card_policy: PtmEvidenceCardPolicy | None = None,
) -> PtmReportBundle:
    """Build the core PTM report bundle from evidence rows and protein context."""

    peptide_entries = tuple(
        sorted(
            (
                PtmReportPeptideEntry(
                    spectrum_id=record.spectrum_id,
                    sample_id=record.sample_id,
                    localized_peptide=record.localized_peptide,
                    canonical_peptide=record.canonical_peptide,
                    sequence=record.sequence,
                    charge=record.charge,
                    score=record.score,
                    q_value=record.q_value,
                    localization_score=record.localization_score,
                    localization_probability=record.localization_probability,
                    protein_refs=record.protein_refs,
                    modification_names=record.modification_names,
                    target_decoy_label=record.target_decoy_label,
                )
                for record in records
            ),
            key=lambda entry: (
                entry.protein_refs[0] if entry.protein_refs else "",
                entry.localized_peptide,
                entry.spectrum_id,
                entry.sample_id or "",
            ),
        )
    )
    mappings = map_ptm_evidence_to_protein_sites(
        records,
        protein_sequences=protein_sequences,
    )
    site_table = build_ptm_site_table(mappings)
    localization_scoring = build_ptm_localization_scoring_report(
        records,
        fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
    )
    site_quantification = None
    differential_analysis = None
    mechanism_classification = None
    motif_enrichment = None
    regulator_enrichment = None
    ortholog_conservation = None
    evidence_cards = None
    evidence_aware_ranking_report = None
    if ortholog_site_records is not None:
        if ortholog_source_species is None or ortholog_target_species is None:
            raise ValueError(
                "ptm ortholog conservation requires explicit source and target species when ortholog_site_records are provided"
            )
        ortholog_conservation = build_ptm_ortholog_conservation_report(
            site_table,
            ortholog_site_records,
            source_species=ortholog_source_species,
            target_species=ortholog_target_species,
        )
    if feature_records is not None:
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_records,
            ambiguity_policy=ambiguity_policy,
        )
    if design_entries is not None:
        if site_quantification is None or feature_records is None:
            raise ValueError(
                "design-aware ptm reporting requires feature_records so site quantification exists before differential analysis"
            )
        differential_analysis = build_ptm_differential_analysis_report(
            site_quantification,
            design_entries,
            normalization_method=normalization_method,
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_records,
            protein_correction_mode=protein_correction_mode,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
        )
        mechanism_classification = build_ptm_mechanism_classification_report(
            differential_analysis
        )
        if any(entry.modification_name == "Phospho" for entry in site_table):
            motif_enrichment = build_ptm_phosphosite_motif_enrichment_report(
                differential_analysis,
                protein_sequences=protein_sequences,
                flank_size=motif_flank_size,
                selection_policy=motif_selection_policy,
                comparison_policy=motif_comparison_policy,
            )
        if annotation_records is not None:
            annotation_mapping_report = build_ptm_site_annotation_mapping_report(
                site_table,
                annotation_records,
                target_species=annotation_target_species,
            )
            regulator_enrichment = build_ptm_regulator_enrichment_report(
                differential_analysis.differential_report,
                annotation_mapping_report,
                policy=regulator_enrichment_policy,
            )
        evidence_cards = build_ptm_evidence_card_report(
            records,
            site_table,
            localization_scoring,
            differential_analysis,
            site_quantification=site_quantification,
            motif_enrichment=motif_enrichment,
            regulator_enrichment=regulator_enrichment,
            mechanism_classification_report=mechanism_classification,
            ortholog_conservation_report=ortholog_conservation,
            protein_records=protein_records,
            protein_sequences=protein_sequences,
            protein_region_context_records=protein_region_context_records,
            policy=evidence_card_policy,
        )
        evidence_aware_ranking_report = _build_ptm_evidence_aware_ranking_report(
            evidence_cards
        )
    return PtmReportBundle(
        peptide_entries=peptide_entries,
        site_table=site_table,
        localization_scoring=localization_scoring,
        site_quantification=site_quantification,
        differential_analysis=differential_analysis,
        mechanism_classification=mechanism_classification,
        motif_enrichment=motif_enrichment,
        regulator_enrichment=regulator_enrichment,
        ortholog_conservation=ortholog_conservation,
        evidence_cards=evidence_cards,
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        summary=PtmReportSummary(
            accepted_evidence_count=len(records),
            peptide_entry_count=len(peptide_entries),
            site_row_count=len(site_table),
            ambiguous_site_count=sum(1 for entry in site_table if entry.ambiguous),
            ambiguous_group_row_count=(
                0
                if site_quantification is None
                or site_quantification.ambiguous_group_quantification is None
                else len(site_quantification.ambiguous_group_quantification.rows)
            ),
            modified_peptide_count=len(
                {
                    entry.localized_peptide
                    for entry in peptide_entries
                }
            ),
            localization_entry_count=len(localization_scoring.entries),
            quantified_site_row_count=(
                0 if site_quantification is None else len(site_quantification.rows)
            ),
            differential_site_count=(
                0
                if differential_analysis is None
                else len(differential_analysis.differential_report.entries)
            ),
            motif_term_count=(
                0 if motif_enrichment is None else len(motif_enrichment.enriched_terms)
            ),
            evidence_card_count=(
                0 if evidence_cards is None else len(evidence_cards.cards)
            ),
            narrative_claim_count=(
                0
                if evidence_cards is None
                else len(evidence_cards.narrative_claims)
            ),
            mechanism_classification_count=(
                0
                if mechanism_classification is None
                else len(mechanism_classification.entries)
            ),
            ortholog_conservation_entry_count=(
                0
                if ortholog_conservation is None
                else len(ortholog_conservation.entries)
            ),
        ),
        note=(
            "ptm reporting assembles governed peptide observations, site rows, "
            "localization review, site quantification, differential analysis, "
            "mechanism classification, motif summaries, and evidence-card ledgers "
            "into one owned report bundle"
        ),
    )


def _build_ptm_evidence_aware_ranking_report(
    evidence_cards: PtmEvidenceCardReport,
) -> EvidenceAwareRankingReport:
    abundance_by_site = {
        card.site_key: max(
            card.differential_result.mean_log2_abundance_a,
            card.differential_result.mean_log2_abundance_b,
        )
        for card in evidence_cards.cards
    }
    abundance_scores = normalize_linear_range(abundance_by_site)
    candidates: list[EvidenceAwareRankingCandidate] = []
    for card in evidence_cards.cards:
        abundance_value = abundance_by_site[card.site_key]
        support_count = len(card.peptide_evidence)
        localization_probability = card.localization.best_localization_probability or 0.0
        support_score = min(
            1.0,
            (0.7 * score_support_count(support_count, saturation=4))
            + (0.3 * localization_probability),
        )
        annotation_score = min(
            1.0,
            (0.2 if card.functional_regions else 0.0)
            + (0.15 if card.motif_evidence.enriched_terms else 0.0)
            + (0.15 if card.regulator_evidence else 0.0)
            + (0.15 if card.crosstalk_partners else 0.0)
            + (0.2 if card.mechanism_classification is not None else 0.0)
            + (
                0.15
                if card.ortholog_conservation is not None
                and card.ortholog_conservation.status.value != "unmapped"
                else 0.0
            ),
        )
        reproducibility_score = min(
            1.0,
            (
                0.5
                * score_support_count(
                    min(
                        card.differential_result.observations_a,
                        card.differential_result.observations_b,
                    ),
                    saturation=3,
                )
            )
            + (
                0.5
                * score_support_count(
                    card.differential_result.complete_pair_count,
                    saturation=3,
                )
            ),
        )
        confidence_score = min(
            1.0,
            (0.7 * _ptm_localization_score(card.localization.localization_tier.value))
            + (0.2 if card.mechanism_classification is not None else 0.0)
            + (
                0.1
                if card.ortholog_conservation is not None
                and card.ortholog_conservation.status.value == "conserved"
                else 0.0
            ),
        )
        penalties: dict[str, float] = {}
        if support_count <= 1:
            penalties["single_peptide_support"] = 0.12
        if abundance_scores[card.site_key] < 0.25:
            penalties["low_abundance_signal"] = 0.1
        if card.differential_result.imputation_dependent_hit:
            penalties["imputation_dependent_hit"] = 0.08
        if card.localization.low_localization:
            penalties["low_localization"] = 0.14
        if card.localization.ambiguous:
            penalties["ambiguous_site"] = 0.08
        if card.localization.shared_peptide:
            penalties["shared_peptide"] = 0.06
        if card.warnings:
            penalties["warning_burden"] = min(0.15, 0.03 * len(card.warnings))
        candidates.append(
            EvidenceAwareRankingCandidate(
                candidate_id=card.site_key,
                entity_kind=EvidenceAwareRankingEntityKind.PTM_SITE,
                display_label=card.site_key,
                effect_size=abs(card.differential_result.log2_fold_change),
                adjusted_p_value=card.differential_result.adjusted_p_value,
                abundance_value=abundance_value,
                support_count=support_count,
                annotation_label=card.modification_name,
                effect_score=score_effect_size(
                    abs(card.differential_result.log2_fold_change),
                    saturation=2.0,
                ),
                significance_score=score_adjusted_p_value(
                    card.differential_result.adjusted_p_value
                ),
                abundance_score=abundance_scores[card.site_key],
                support_score=support_score,
                qc_score=reproducibility_score,
                annotation_score=annotation_score,
                reproducibility_score=reproducibility_score,
                confidence_score=confidence_score,
                penalties=penalties,
                uncertainty=_ptm_result_uncertainty(card),
                source_ids=(card.card_id, *card.claim_ids),
                note=(
                    "ptm ranking combines site effect, localization, peptide support, "
                    "mechanism context, ortholog context, and evidence-card warnings"
                ),
            )
        )
    return build_evidence_aware_ranking_report(tuple(candidates))


def _ptm_localization_score(value: str) -> float:
    return {
        "high_confidence": 1.0,
        "medium_confidence": 0.75,
        "low_confidence": 0.45,
        "refused": 0.15,
    }.get(value, 0.4)


def _ptm_result_uncertainty(card) -> float:
    uncertainty = 0.0
    if card.differential_result.adjusted_p_value is None:
        uncertainty += 0.08
    if card.differential_result.uncertainty_note:
        uncertainty += 0.08
    if card.localization.low_localization:
        uncertainty += 0.08
    if len(card.peptide_evidence) <= 1:
        uncertainty += 0.06
    return min(0.35, uncertainty)


def render_ptm_report_summary_tsv(report: PtmReportBundle) -> str:
    """Render compact PTM report summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "accepted_evidence_count",
            "peptide_entry_count",
            "site_row_count",
            "ambiguous_site_count",
            "ambiguous_group_row_count",
            "modified_peptide_count",
            "localization_entry_count",
            "quantified_site_row_count",
            "differential_site_count",
            "motif_term_count",
            "evidence_card_count",
            "narrative_claim_count",
            "mechanism_classification_count",
            "ortholog_conservation_entry_count",
        ]
    )
    writer.writerow(
        [
            report.summary.accepted_evidence_count,
            report.summary.peptide_entry_count,
            report.summary.site_row_count,
            report.summary.ambiguous_site_count,
            report.summary.ambiguous_group_row_count,
            report.summary.modified_peptide_count,
            report.summary.localization_entry_count,
            report.summary.quantified_site_row_count,
            report.summary.differential_site_count,
            report.summary.motif_term_count,
            report.summary.evidence_card_count,
            report.summary.narrative_claim_count,
            report.summary.mechanism_classification_count,
            report.summary.ortholog_conservation_entry_count,
        ]
    )
    return buffer.getvalue()


def render_ptm_report_peptide_tsv(report: PtmReportBundle) -> str:
    """Render the PTM peptide-observation table as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "spectrum_id",
            "sample_id",
            "localized_peptide",
            "canonical_peptide",
            "sequence",
            "charge",
            "score",
            "q_value",
            "localization_score",
            "localization_probability",
            "protein_refs",
            "modification_names",
            "target_decoy_label",
        ]
    )
    for entry in sort_rows_by_fields(
        report.peptide_entries,
        "spectrum_id",
        "sample_id",
        "canonical_peptide",
    ):
        writer.writerow(
            [
                entry.spectrum_id,
                entry.sample_id or "",
                entry.localized_peptide,
                entry.canonical_peptide,
                entry.sequence,
                entry.charge,
                entry.score,
                "" if entry.q_value is None else entry.q_value,
                entry.localization_score,
                ""
                if entry.localization_probability is None
                else entry.localization_probability,
                ";".join(sort_strings(entry.protein_refs)),
                ";".join(sort_strings(entry.modification_names)),
                entry.target_decoy_label.value,
            ]
        )
    return buffer.getvalue()


def render_ptm_report_localization_tsv(report: PtmReportBundle) -> str:
    """Render the PTM localization review table as TSV."""

    return render_ptm_localization_scoring_entry_tsv(report.localization_scoring)


def render_ptm_report_site_quant_matrix_tsv(report: PtmReportBundle) -> str:
    """Render the PTM site-quant matrix section as TSV."""

    if report.site_quantification is None:
        raise ValueError("ptm report bundle does not include site quantification")
    return render_ptm_site_quant_matrix_tsv(report.site_quantification)


def render_ptm_report_differential_tsv(report: PtmReportBundle) -> str:
    """Render the PTM differential-results section as TSV."""

    if report.differential_analysis is None:
        raise ValueError("ptm report bundle does not include differential analysis")
    return render_ptm_site_differential_tsv(
        report.differential_analysis.differential_report
    )


def render_ptm_report_evidence_aware_ranking_tsv(report: PtmReportBundle) -> str:
    """Render the PTM evidence-aware ranking section as TSV."""

    if report.evidence_aware_ranking_report is None:
        raise ValueError("ptm report bundle does not include evidence-aware ranking")
    return render_evidence_aware_ranking_tsv(report.evidence_aware_ranking_report)


def export_ptm_report_bundle(
    report: PtmReportBundle,
    output_dir: Path,
) -> PtmReportExportManifest:
    """Write one PTM report bundle into a stable output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_name = "ptm_report_summary.tsv"
    peptide_name = "ptm_peptides.tsv"
    site_name = "ptm_sites.tsv"
    localization_name = "ptm_localization.tsv"
    (output_dir / summary_name).write_text(
        render_ptm_report_summary_tsv(report),
        encoding="utf-8",
    )
    (output_dir / peptide_name).write_text(
        render_ptm_report_peptide_tsv(report),
        encoding="utf-8",
    )
    (output_dir / site_name).write_text(
        render_ptm_site_table_tsv(report.site_table),
        encoding="utf-8",
    )
    (output_dir / localization_name).write_text(
        render_ptm_report_localization_tsv(report),
        encoding="utf-8",
    )

    site_quant_matrix_name = None
    site_quant_missingness_name = None
    site_group_summary_name = None
    site_group_matrix_name = None
    site_group_missingness_name = None
    if report.site_quantification is not None:
        site_quant_matrix_name = "ptm_site_quant_matrix.tsv"
        site_quant_missingness_name = "ptm_site_quant_missingness.tsv"
        (output_dir / site_quant_matrix_name).write_text(
            render_ptm_report_site_quant_matrix_tsv(report),
            encoding="utf-8",
        )
        (output_dir / site_quant_missingness_name).write_text(
            render_ptm_site_quant_missingness_tsv(report.site_quantification),
            encoding="utf-8",
        )
        if report.site_quantification.ambiguous_group_quantification is not None:
            site_group_summary_name = "ptm_site_group_summary.tsv"
            site_group_matrix_name = "ptm_site_group_matrix.tsv"
            site_group_missingness_name = "ptm_site_group_missingness.tsv"
            (output_dir / site_group_summary_name).write_text(
                render_ptm_site_group_quant_summary_tsv(
                    report.site_quantification.ambiguous_group_quantification
                ),
                encoding="utf-8",
            )
            (output_dir / site_group_matrix_name).write_text(
                render_ptm_site_group_quant_matrix_tsv(
                    report.site_quantification.ambiguous_group_quantification
                ),
                encoding="utf-8",
            )
            (output_dir / site_group_missingness_name).write_text(
                render_ptm_site_group_quant_missingness_tsv(
                    report.site_quantification.ambiguous_group_quantification
                ),
                encoding="utf-8",
            )

    differential_name = None
    volcano_name = None
    if report.differential_analysis is not None:
        differential_name = "ptm_differential.tsv"
        volcano_name = "ptm_differential_volcano.tsv"
        (output_dir / differential_name).write_text(
            render_ptm_report_differential_tsv(report),
            encoding="utf-8",
        )
        (output_dir / volcano_name).write_text(
            render_ptm_differential_volcano_tsv(
                report.differential_analysis.volcano_plot
            ),
            encoding="utf-8",
        )

    motif_window_name = None
    motif_frequency_name = None
    motif_term_name = None
    motif_logo_name = None
    if report.motif_enrichment is not None:
        motif_window_name = "ptm_motif_windows.tsv"
        motif_frequency_name = "ptm_motif_frequency.tsv"
        motif_term_name = "ptm_motif_terms.tsv"
        motif_logo_name = "ptm_motif_logo.tsv"
        (output_dir / motif_window_name).write_text(
            render_ptm_phosphosite_motif_window_tsv(report.motif_enrichment),
            encoding="utf-8",
        )
        (output_dir / motif_frequency_name).write_text(
            render_ptm_phosphosite_motif_frequency_tsv(report.motif_enrichment),
            encoding="utf-8",
        )
        (output_dir / motif_term_name).write_text(
            render_ptm_phosphosite_motif_enriched_term_tsv(report.motif_enrichment),
            encoding="utf-8",
        )
        (output_dir / motif_logo_name).write_text(
            render_ptm_phosphosite_motif_logo_tsv(report.motif_enrichment),
            encoding="utf-8",
        )

    regulator_enrichment_summary_name = None
    regulator_enrichment_name = None
    if report.regulator_enrichment is not None:
        regulator_enrichment_summary_name = "ptm_regulator_enrichment_summary.tsv"
        regulator_enrichment_name = "ptm_regulator_enrichment.tsv"
        (output_dir / regulator_enrichment_summary_name).write_text(
            render_ptm_regulator_enrichment_summary_tsv(report.regulator_enrichment),
            encoding="utf-8",
        )
        (output_dir / regulator_enrichment_name).write_text(
            render_ptm_regulator_enrichment_tsv(report.regulator_enrichment),
            encoding="utf-8",
        )

    mechanism_classification_summary_name = None
    mechanism_classification_name = None
    if report.mechanism_classification is not None:
        mechanism_classification_summary_name = "ptm_mechanism_classification_summary.tsv"
        mechanism_classification_name = "ptm_mechanism_classification.tsv"
        (output_dir / mechanism_classification_summary_name).write_text(
            render_ptm_mechanism_classification_summary_tsv(
                report.mechanism_classification
            ),
            encoding="utf-8",
        )
        (output_dir / mechanism_classification_name).write_text(
            render_ptm_mechanism_classification_tsv(report.mechanism_classification),
            encoding="utf-8",
        )

    ortholog_conservation_summary_name = None
    ortholog_conservation_name = None
    if report.ortholog_conservation is not None:
        ortholog_conservation_summary_name = "ptm_ortholog_conservation_summary.tsv"
        ortholog_conservation_name = "ptm_ortholog_conservation.tsv"
        (output_dir / ortholog_conservation_summary_name).write_text(
            render_ptm_ortholog_conservation_summary_tsv(report.ortholog_conservation),
            encoding="utf-8",
        )
        (output_dir / ortholog_conservation_name).write_text(
            render_ptm_ortholog_conservation_tsv(report.ortholog_conservation),
            encoding="utf-8",
        )

    evidence_card_summary_name = None
    evidence_card_name = None
    evidence_claim_name = None
    evidence_aware_ranking_name = None
    if report.evidence_cards is not None:
        evidence_card_summary_name = "ptm_evidence_card_summary.tsv"
        evidence_card_name = "ptm_evidence_cards.tsv"
        evidence_claim_name = "ptm_evidence_claims.tsv"
        (output_dir / evidence_card_summary_name).write_text(
            render_ptm_evidence_card_summary_tsv(report.evidence_cards),
            encoding="utf-8",
        )
        (output_dir / evidence_card_name).write_text(
            render_ptm_evidence_card_tsv(report.evidence_cards),
            encoding="utf-8",
        )
        (output_dir / evidence_claim_name).write_text(
            render_ptm_evidence_claim_tsv(report.evidence_cards),
            encoding="utf-8",
        )
    if report.evidence_aware_ranking_report is not None:
        evidence_aware_ranking_name = "ptm_evidence_aware_ranking.tsv"
        (output_dir / evidence_aware_ranking_name).write_text(
            render_ptm_report_evidence_aware_ranking_tsv(report),
            encoding="utf-8",
        )

    return PtmReportExportManifest(
        summary=report.summary,
        artifacts=PtmReportArtifactPaths(
            summary_tsv=summary_name,
            peptide_tsv=peptide_name,
            site_tsv=site_name,
            localization_tsv=localization_name,
            site_quant_matrix_tsv=site_quant_matrix_name,
            site_quant_missingness_tsv=site_quant_missingness_name,
            site_group_summary_tsv=site_group_summary_name,
            site_group_matrix_tsv=site_group_matrix_name,
            site_group_missingness_tsv=site_group_missingness_name,
            differential_tsv=differential_name,
            differential_volcano_tsv=volcano_name,
            motif_window_tsv=motif_window_name,
            motif_frequency_tsv=motif_frequency_name,
            motif_term_tsv=motif_term_name,
            motif_logo_tsv=motif_logo_name,
            regulator_enrichment_summary_tsv=regulator_enrichment_summary_name,
            regulator_enrichment_tsv=regulator_enrichment_name,
            mechanism_classification_summary_tsv=mechanism_classification_summary_name,
            mechanism_classification_tsv=mechanism_classification_name,
            ortholog_conservation_summary_tsv=ortholog_conservation_summary_name,
            ortholog_conservation_tsv=ortholog_conservation_name,
            evidence_card_summary_tsv=evidence_card_summary_name,
            evidence_card_tsv=evidence_card_name,
            evidence_claim_tsv=evidence_claim_name,
            evidence_aware_ranking_tsv=evidence_aware_ranking_name,
        ),
        motif_summary_included=report.motif_enrichment is not None,
        note=(
            "ptm report export writes stable peptide, site, localization, quantification, differential, motif, regulator, and evidence-card files into one durable output directory"
        ),
    )
