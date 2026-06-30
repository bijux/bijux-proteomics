# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Report assembly for PTM evidence-card surfaces."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import (
    build_ptm_card_id,
    build_ptm_claim_id,
    build_site_id,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields
from bijux_proteomics.ptm.cards.evidence_cards.models import (
    PtmEvidenceCard,
    PtmEvidenceCardClaim,
    PtmEvidenceCardClaimKind,
    PtmEvidenceCardDifferentialResult,
    PtmEvidenceCardMechanismClassification,
    PtmEvidenceCardMotifEvidence,
    PtmEvidenceCardPolicy,
    PtmEvidenceCardProteinCorrection,
    PtmEvidenceCardRegulatorEvidence,
    PtmEvidenceCardReport,
    PtmEvidenceCardSummary,
)
from bijux_proteomics.ptm.cards.evidence_cards.site_evidence import (
    build_card_warnings,
    build_crosstalk_partners_by_site,
    build_identity_entries_by_site,
    build_localization_evidence,
    build_mechanism_classification_by_site,
    build_motif_evidence,
    build_ortholog_conservation_by_site,
    build_peptide_evidence,
    build_quantification_evidence,
    build_source_row_lineage_for_site,
)
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord, PtmSiteEntry
from bijux_proteomics.ptm.differential_analysis import (
    PtmDifferentialAnalysisReport,
    PtmSiteDifferentialEntry,
)
from bijux_proteomics.ptm.mechanism_classification import PtmMechanismClassificationReport
from bijux_proteomics.ptm.motif_analysis import PtmPhosphositeMotifEnrichmentReport
from bijux_proteomics.ptm.ortholog_site_conservation import PtmOrthologConservationReport
from bijux_proteomics.ptm.regulator_enrichment import (
    PtmRegulatorEnrichmentEntry,
    PtmRegulatorEnrichmentReport,
)
from bijux_proteomics.ptm.site_annotation_import import PtmSiteAnnotationMappingReport
from bijux_proteomics.ptm.site_quantification import PtmSiteQuantificationReport
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_identity_resolution import ProteinIdentityLevel
from bijux_proteomics.sequences.protein_region_context_models import (
    ProteinFunctionalRegionEvidence,
    ProteinRegionContextRecord,
    ProteinSiteRegionReference,
)
from bijux_proteomics.sequences.protein_region_context_workflows import (
    build_protein_site_region_context_report,
)
from bijux_proteomics.ptm.localization_scoring import PtmLocalizationScoringReport

_SOURCE_ROW_LINEAGE_TOKENS = (
    "source_row_refs",
    "derived_no_source_reason",
    "SourceRowLineage",
)


def build_ptm_evidence_card_report(
    records: tuple[PtmEvidenceRecord, ...],
    site_entries: tuple[PtmSiteEntry, ...],
    localization_scoring: PtmLocalizationScoringReport,
    differential_analysis: PtmDifferentialAnalysisReport,
    *,
    site_quantification: PtmSiteQuantificationReport | None = None,
    motif_enrichment: PtmPhosphositeMotifEnrichmentReport | None = None,
    regulator_enrichment: PtmRegulatorEnrichmentReport | None = None,
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None = None,
    mechanism_classification_report: PtmMechanismClassificationReport | None = None,
    ortholog_conservation_report: PtmOrthologConservationReport | None = None,
    protein_records: tuple[NormalizedProteinRecord, ...] | None = None,
    protein_sequences: dict[str, str] | None = None,
    protein_region_context_records: tuple[ProteinRegionContextRecord, ...]
    | None = None,
    policy: PtmEvidenceCardPolicy | None = None,
) -> PtmEvidenceCardReport:
    """Build one PTM evidence-card report over significant differential sites."""
    active_policy = policy or PtmEvidenceCardPolicy()
    site_entry_by_key = {entry.site_key: entry for entry in site_entries}
    quant_row_by_key = (
        {row.site_key: row for row in site_quantification.rows}
        if site_quantification is not None
        else {}
    )
    differential_entries = tuple(
        entry
        for entry in differential_analysis.differential_report.entries
        if entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= active_policy.max_adjusted_p_value
    )
    regulator_entries_by_site: dict[str, list[PtmRegulatorEnrichmentEntry]] = {}
    if regulator_enrichment is not None:
        for entry in regulator_enrichment.entries:
            for site_key in entry.supporting_sites:
                regulator_entries_by_site.setdefault(site_key, []).append(entry)
    functional_context_by_site: dict[
        str, tuple[ProteinFunctionalRegionEvidence, ...]
    ] = {}
    if protein_region_context_records:
        functional_context_report = build_protein_site_region_context_report(
            tuple(
                ProteinSiteRegionReference(
                    site_key=site_entry.site_key,
                    protein_ref=site_entry.protein_ref,
                    position=site_entry.position,
                )
                for site_entry in site_entries
            ),
            protein_region_context_records,
        )
        functional_context_by_site = {
            entry.site_key: entry.functional_regions
            for entry in functional_context_report.entries
        }
    identity_entries_by_site = build_identity_entries_by_site(
        records,
        site_entries=site_entries,
        protein_records=protein_records,
        protein_sequences=protein_sequences,
    )
    crosstalk_partners_by_site = build_crosstalk_partners_by_site(
        site_entries,
        differential_analysis.differential_report,
        annotation_mapping_report=annotation_mapping_report,
    )
    mechanism_classification_by_site = build_mechanism_classification_by_site(
        mechanism_classification_report
    )
    ortholog_conservation_by_site = build_ortholog_conservation_by_site(
        ortholog_conservation_report
    )

    cards: list[PtmEvidenceCard] = []
    narrative_claims: list[PtmEvidenceCardClaim] = []
    for differential_entry in sort_rows_by_fields(
        differential_entries,
        "protein_ref",
        "position",
        "modification_name",
        "site_key",
    ):
        site_entry = site_entry_by_key[differential_entry.site_key]
        source_row_lineage = build_source_row_lineage_for_site(records, site_entry)
        peptide_evidence = build_peptide_evidence(records, site_entry)
        identity_entry = identity_entries_by_site.get(differential_entry.site_key)
        localization = build_localization_evidence(
            localization_scoring.entries,
            differential_entry=differential_entry,
            site_entry=site_entry,
        )
        quantification = build_quantification_evidence(
            quant_row_by_key.get(differential_entry.site_key)
        )
        motif_evidence = build_motif_evidence(
            motif_enrichment,
            site_key=differential_entry.site_key,
        )
        regulators = tuple(
            PtmEvidenceCardRegulatorEvidence(
                regulator=entry.regulator,
                regulator_kind=entry.regulator_kind,
                direction=entry.direction.value,
                adjusted_p_value=entry.adjusted_p_value,
                p_value=entry.p_value,
                enrichment_ratio=entry.enrichment_ratio,
                annotation_coverage_fraction=entry.annotation_coverage_fraction,
            )
            for entry in sort_rows_by_fields(
                tuple(regulator_entries_by_site.get(differential_entry.site_key, ())),
                "adjusted_p_value",
                "p_value",
                "direction",
                "regulator_kind",
                "regulator",
            )
        )
        warnings = build_card_warnings(
            differential_entry=differential_entry,
            site_entry=site_entry,
        )
        site_id = build_site_id(
            differential_entry.protein_ref,
            differential_entry.residue,
            differential_entry.position,
            differential_entry.modification_name,
        )
        card_id = _build_card_id(differential_entry, site_id=site_id)
        claim_id = _build_claim_id(differential_entry, site_id=site_id)
        cards.append(
            PtmEvidenceCard(
                card_id=card_id,
                site_key=differential_entry.site_key,
                protein_ref=differential_entry.protein_ref,
                residue=differential_entry.residue,
                position=differential_entry.position,
                modification_name=differential_entry.modification_name,
                target_decoy_label=site_entry.target_decoy_label,
                identity_level=(
                    ProteinIdentityLevel.AMBIGUOUS
                    if identity_entry is None
                    else identity_entry.identity_level
                ),
                identity_reason=(
                    "no protein identity support was available for this PTM site"
                    if identity_entry is None
                    else identity_entry.identity_reason
                ),
                peptide_evidence=peptide_evidence,
                localization=localization,
                quantification=quantification,
                differential_result=PtmEvidenceCardDifferentialResult(
                    condition_a=differential_entry.condition_a,
                    condition_b=differential_entry.condition_b,
                    observations_a=differential_entry.observations_a,
                    observations_b=differential_entry.observations_b,
                    complete_pair_count=differential_entry.complete_pair_count,
                    mean_log2_abundance_a=differential_entry.mean_log2_abundance_a,
                    mean_log2_abundance_b=differential_entry.mean_log2_abundance_b,
                    log2_fold_change=differential_entry.log2_fold_change,
                    p_value=differential_entry.p_value,
                    adjusted_p_value=differential_entry.adjusted_p_value,
                    standard_error=differential_entry.standard_error,
                    confidence_interval_low=differential_entry.confidence_interval_low,
                    confidence_interval_high=differential_entry.confidence_interval_high,
                    effect_size_cohens_d=differential_entry.effect_size_cohens_d,
                    imputation_dependent_hit=differential_entry.imputation_dependent_hit,
                    uncertainty_note=differential_entry.uncertainty_note,
                ),
                motif_evidence=motif_evidence,
                regulator_evidence=regulators,
                crosstalk_partners=crosstalk_partners_by_site.get(
                    differential_entry.site_key,
                    (),
                ),
                mechanism_classification=mechanism_classification_by_site.get(
                    differential_entry.site_key
                ),
                ortholog_conservation=ortholog_conservation_by_site.get(
                    differential_entry.site_key
                ),
                functional_regions=functional_context_by_site.get(
                    differential_entry.site_key,
                    (),
                ),
                protein_correction=PtmEvidenceCardProteinCorrection(
                    mode=differential_analysis.protein_correction_mode,
                    status=differential_entry.protein_correction_status,
                    protein_log2_fold_change=differential_entry.protein_log2_fold_change,
                    protein_adjusted_p_value=differential_entry.protein_adjusted_p_value,
                    corrected_log2_fold_change=differential_entry.corrected_log2_fold_change,
                ),
                warnings=warnings,
                claim_ids=(claim_id,),
                source_row_refs=source_row_lineage.source_row_refs,
                derived_no_source_reason=source_row_lineage.derived_no_source_reason,
            )
        )
        narrative_claims.append(
            PtmEvidenceCardClaim(
                claim_id=claim_id,
                card_id=card_id,
                site_key=differential_entry.site_key,
                claim_kind=PtmEvidenceCardClaimKind.DIFFERENTIAL_SITE,
                text=_build_claim_text(
                    differential_entry,
                    motif_evidence=motif_evidence,
                    regulators=regulators,
                ),
                source_row_refs=source_row_lineage.source_row_refs,
                derived_no_source_reason=source_row_lineage.derived_no_source_reason,
            )
        )

    stable_cards = tuple(
        sorted(
            cards,
            key=lambda entry: (
                entry.protein_ref,
                entry.position,
                entry.modification_name,
                entry.card_id,
            ),
        )
    )
    stable_claims = tuple(
        sorted(
            narrative_claims,
            key=lambda entry: (
                entry.site_key,
                entry.claim_id,
            ),
        )
    )
    return PtmEvidenceCardReport(
        condition_a=differential_analysis.differential_report.condition_a,
        condition_b=differential_analysis.differential_report.condition_b,
        policy=active_policy,
        cards=stable_cards,
        narrative_claims=stable_claims,
        summary=PtmEvidenceCardSummary(
            significant_site_count=len(differential_entries),
            card_count=len(stable_cards),
            narrative_claim_count=len(stable_claims),
            regulator_supported_card_count=sum(
                1 for entry in stable_cards if entry.regulator_evidence
            ),
            motif_annotated_card_count=sum(
                1 for entry in stable_cards if entry.motif_evidence.centered_windows
            ),
            crosstalk_supported_card_count=sum(
                1 for entry in stable_cards if entry.crosstalk_partners
            ),
            mechanism_classified_card_count=sum(
                1
                for entry in stable_cards
                if entry.mechanism_classification is not None
            ),
            ortholog_context_card_count=sum(
                1 for entry in stable_cards if entry.ortholog_conservation is not None
            ),
            functional_context_card_count=sum(
                1 for entry in stable_cards if entry.functional_regions
            ),
            warning_card_count=sum(1 for entry in stable_cards if entry.warnings),
        ),
        note=(
            "ptm evidence cards preserve one structured object per significant site, "
            "carry peptide, localization, quantification, differential, mechanism "
            "classification, motif, crosstalk, ortholog-site conservation, "
            "functional-region, regulator, and protein-correction evidence together, "
            "and link every narrative claim back to a stable card id"
        ),
    )


def _build_card_id(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    site_id: str,
) -> str:
    return build_ptm_card_id(
        site_id,
        differential_entry.condition_a,
        differential_entry.condition_b,
    )


def _build_claim_id(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    site_id: str,
) -> str:
    return build_ptm_claim_id(
        site_id,
        differential_entry.condition_a,
        differential_entry.condition_b,
    )


def _build_claim_text(
    differential_entry: PtmSiteDifferentialEntry,
    *,
    motif_evidence: PtmEvidenceCardMotifEvidence,
    regulators: tuple[PtmEvidenceCardRegulatorEvidence, ...],
) -> str:
    condition_phrase = (
        f"{differential_entry.condition_b} versus {differential_entry.condition_a}"
    )
    fragments = [
        (
            f"{differential_entry.site_key} changed in {condition_phrase} "
            f"with log2 fold change {differential_entry.log2_fold_change:.3g} "
            f"and adjusted p-value {differential_entry.adjusted_p_value:.3g}"
        )
    ]
    if motif_evidence.centered_windows:
        fragments.append(
            f"motif window {motif_evidence.centered_windows[0]} supports sequence context"
        )
    if regulators:
        fragments.append(
            "linked regulators include "
            + ", ".join(
                f"{entry.regulator} ({entry.direction})" for entry in regulators[:3]
            )
        )
    return "; ".join(fragments)
