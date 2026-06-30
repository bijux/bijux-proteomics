# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Site-evidence assembly support for PTM evidence cards."""

from __future__ import annotations

from bijux_proteomics.domain.source_row_lineage import SourceRowLineage
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.ptm.cards.evidence_cards.models import (
    PtmEvidenceCardCrosstalkPartner,
    PtmEvidenceCardLocalization,
    PtmEvidenceCardLocalizationObservation,
    PtmEvidenceCardMechanismClassification,
    PtmEvidenceCardMotifEvidence,
    PtmEvidenceCardOrthologConservation,
    PtmEvidenceCardPeptideObservation,
    PtmEvidenceCardQuantification,
    PtmEvidenceCardSampleValue,
    PtmEvidenceCardWarning,
    PtmEvidenceCardWarningCode,
)
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord, PtmSiteEntry
from bijux_proteomics.ptm.crosstalk import build_ptm_crosstalk_report
from bijux_proteomics.ptm.differential_analysis import (
    PtmProteinCorrectionStatus,
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
)
from bijux_proteomics.ptm.localization_scoring import PtmLocalizationScoringEntry
from bijux_proteomics.ptm.mechanism_classification import (
    PtmMechanismClassificationReport,
)
from bijux_proteomics.ptm.motif_analysis import PtmPhosphositeMotifEnrichmentReport
from bijux_proteomics.ptm.ortholog_site_conservation import (
    PtmOrthologConservationReport,
)
from bijux_proteomics.ptm.site_annotation_import import PtmSiteAnnotationMappingReport
from bijux_proteomics.ptm.site_quantification import PtmSiteQuantRow
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.sequences.fasta import NormalizedProteinRecord
from bijux_proteomics.sequences.protein_identity_resolution import (
    ProteinIdentityReference,
    ProteinIdentityResolutionEntry,
    build_protein_identity_resolution_report,
)


def build_peptide_evidence(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceCardPeptideObservation, ...]:
    observations = tuple(
        PtmEvidenceCardPeptideObservation(
            spectrum_id=record.spectrum_id,
            sample_id=record.sample_id,
            localized_peptide=record.localized_peptide,
            canonical_peptide=record.canonical_peptide,
            charge=record.charge,
            score=record.score,
            q_value=record.q_value,
            protein_refs=record.protein_refs,
        )
        for record in matching_records_for_site(records, site_entry)
    )
    return tuple(
        sort_rows_by_fields(
            observations,
            "spectrum_id",
            "sample_id",
            "localized_peptide",
        )
    )


def build_source_row_lineage_for_site(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> SourceRowLineage:
    matching_records = matching_records_for_site(records, site_entry)
    if matching_records:
        return SourceRowLineage.from_imported_provenances(
            tuple(record.provenance for record in matching_records)
        )
    return SourceRowLineage.from_imported_provenances(
        (site_entry.provenance,),
        derived_no_source_reason=(
            "ptm evidence cards summarize governed site-level differential evidence but exact source-row pairs were not retained after site aggregation"
        ),
    )


def matching_records_for_site(
    records: tuple[PtmEvidenceRecord, ...],
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceRecord, ...]:
    return tuple(
        record
        for record in records
        if site_entry.protein_ref in record.protein_refs
        and record.localized_peptide in site_entry.localized_peptides
        and site_entry.modification_name in record.modification_names
    )


def build_localization_evidence(
    localization_entries: tuple[PtmLocalizationScoringEntry, ...],
    *,
    differential_entry: PtmSiteDifferentialEntry,
    site_entry: PtmSiteEntry,
) -> PtmEvidenceCardLocalization:
    observations = tuple(
        PtmEvidenceCardLocalizationObservation(
            spectrum_id=entry.spectrum_id,
            sample_id=entry.sample_id,
            localized_peptide=entry.localized_peptide,
            peptide_site_index=entry.peptide_site_index,
            candidate_site_indices=entry.candidate_site_indices,
            ambiguity_group=entry.ambiguity_group,
            localization_probability=entry.localization_probability,
            probability_source=entry.probability_source,
            localization_tier=entry.localization_tier,
            supported_site_determining_ions=entry.supported_site_determining_ions,
        )
        for entry in localization_entries
        if entry.localized_peptide in site_entry.localized_peptides
        and entry.modification_name == differential_entry.modification_name
    )
    stable_observations = tuple(
        sort_rows_by_fields(
            observations,
            "spectrum_id",
            "peptide_site_index",
            "localized_peptide",
        )
    )
    probabilities = tuple(
        sorted(
            {
                observation.localization_probability
                for observation in stable_observations
            }
        )
    )
    return PtmEvidenceCardLocalization(
        localization_tier=differential_entry.localization_tier,
        low_localization=differential_entry.low_localization,
        ambiguous=differential_entry.ambiguous,
        shared_peptide=differential_entry.shared_peptide,
        localized_peptides=site_entry.localized_peptides,
        observations=stable_observations,
        best_localization_probability=(
            None if not probabilities else probabilities[-1]
        ),
        supported_site_determining_ion_count=sum(
            len(observation.supported_site_determining_ions)
            for observation in stable_observations
        ),
    )


def build_identity_entries_by_site(
    records: tuple[PtmEvidenceRecord, ...],
    *,
    site_entries: tuple[PtmSiteEntry, ...],
    protein_records: tuple[NormalizedProteinRecord, ...] | None,
    protein_sequences: dict[str, str] | None,
) -> dict[str, ProteinIdentityResolutionEntry]:
    if not protein_records and not protein_sequences:
        return {}
    references: list[ProteinIdentityReference] = []
    for site_entry in site_entries:
        peptide_evidence = build_peptide_evidence(records, site_entry)
        references.append(
            ProteinIdentityReference(
                evidence_key=site_entry.site_key,
                target_protein_ref=site_entry.protein_ref,
                candidate_protein_refs=tuple(
                    dict.fromkeys(
                        (
                            site_entry.protein_ref,
                            *(
                                protein_ref
                                for observation in peptide_evidence
                                for protein_ref in observation.protein_refs
                            ),
                        )
                    )
                ),
                peptide_sequences=tuple(
                    dict.fromkeys(
                        observation.canonical_peptide
                        for observation in peptide_evidence
                    )
                ),
            )
        )
    report = build_protein_identity_resolution_report(
        tuple(references),
        protein_records=() if protein_records is None else protein_records,
        protein_sequences=protein_sequences,
    )
    return {entry.evidence_key: entry for entry in report.entries}


def build_crosstalk_partners_by_site(
    site_entries: tuple[PtmSiteEntry, ...],
    differential_report: PtmSiteDifferentialReport,
    *,
    annotation_mapping_report: PtmSiteAnnotationMappingReport | None = None,
) -> dict[str, tuple[PtmEvidenceCardCrosstalkPartner, ...]]:
    crosstalk_report = build_ptm_crosstalk_report(
        site_entries,
        differential_report,
        annotation_mapping_report=annotation_mapping_report,
    )
    partners_by_site: dict[str, list[PtmEvidenceCardCrosstalkPartner]] = {}
    for entry in crosstalk_report.entries:
        partners_by_site.setdefault(entry.left_site_key, []).append(
            PtmEvidenceCardCrosstalkPartner(
                partner_site_key=entry.right_site_key,
                partner_protein_ref=entry.right_protein_ref,
                partner_modification_name=entry.right_modification_name,
                partner_position=entry.right_position,
                partner_log2_fold_change=entry.right_log2_fold_change,
                relationship=entry.relationship,
                evidence_sources=entry.evidence_sources,
                shared_peptides=entry.shared_peptides,
                shared_pathways=entry.shared_pathways,
                residue_distance=entry.residue_distance,
                evidence_note=entry.evidence_note,
            )
        )
        partners_by_site.setdefault(entry.right_site_key, []).append(
            PtmEvidenceCardCrosstalkPartner(
                partner_site_key=entry.left_site_key,
                partner_protein_ref=entry.left_protein_ref,
                partner_modification_name=entry.left_modification_name,
                partner_position=entry.left_position,
                partner_log2_fold_change=entry.left_log2_fold_change,
                relationship=entry.relationship,
                evidence_sources=entry.evidence_sources,
                shared_peptides=entry.shared_peptides,
                shared_pathways=entry.shared_pathways,
                residue_distance=entry.residue_distance,
                evidence_note=entry.evidence_note,
            )
        )
    return {
        site_key: tuple(sorted(partners, key=lambda partner: partner.partner_site_key))
        for site_key, partners in partners_by_site.items()
    }


def build_mechanism_classification_by_site(
    mechanism_classification_report: PtmMechanismClassificationReport | None,
) -> dict[str, PtmEvidenceCardMechanismClassification]:
    if mechanism_classification_report is None:
        return {}
    return {
        entry.site_key: PtmEvidenceCardMechanismClassification(
            mechanism_class=entry.mechanism_class,
            reason_codes=entry.reason_codes,
            raw_log2_fold_change=entry.raw_log2_fold_change,
            corrected_log2_fold_change=entry.corrected_log2_fold_change,
            protein_log2_fold_change=entry.protein_log2_fold_change,
            protein_adjusted_p_value=entry.protein_adjusted_p_value,
            note=entry.note,
        )
        for entry in mechanism_classification_report.entries
    }


def build_ortholog_conservation_by_site(
    ortholog_conservation_report: PtmOrthologConservationReport | None,
) -> dict[str, PtmEvidenceCardOrthologConservation]:
    if ortholog_conservation_report is None:
        return {}
    return {
        entry.site_key: PtmEvidenceCardOrthologConservation(
            status=entry.status,
            source_species=entry.source_species,
            target_species=entry.target_species,
            ortholog_target_site_keys=entry.ortholog_target_site_keys,
            ortholog_target_protein_refs=entry.ortholog_target_protein_refs,
            ortholog_target_positions=entry.ortholog_target_positions,
            evidence_labels=entry.evidence_labels,
            source_names=entry.source_names,
            source_accessions=entry.source_accessions,
            note=entry.note,
        )
        for entry in ortholog_conservation_report.entries
    }


def build_quantification_evidence(
    quant_row: PtmSiteQuantRow | None,
) -> PtmEvidenceCardQuantification | None:
    if quant_row is None:
        return None
    sample_values = tuple(
        PtmEvidenceCardSampleValue(
            sample_id=value.sample_id,
            abundance=value.abundance,
            missing_value_kind=value.missing_value_kind,
            contributing_feature_count=value.contributing_feature_count,
        )
        for value in quant_row.values
    )
    return PtmEvidenceCardQuantification(
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


def build_motif_evidence(
    motif_enrichment: PtmPhosphositeMotifEnrichmentReport | None,
    *,
    site_key: str,
) -> PtmEvidenceCardMotifEvidence:
    if motif_enrichment is None:
        return PtmEvidenceCardMotifEvidence()
    matching_windows = tuple(
        sort_strings(
            tuple(
                window.centered_window
                for window in motif_enrichment.regulated_windows
                if window.site_key == site_key
            )
        )
    )
    enriched_terms = (
        tuple(
            f"{entry.position_offset:+d}:{entry.residue}"
            for entry in motif_enrichment.enriched_terms
        )
        if matching_windows
        else ()
    )
    return PtmEvidenceCardMotifEvidence(
        centered_windows=matching_windows,
        enriched_terms=enriched_terms,
    )


def build_card_warnings(
    *,
    differential_entry: PtmSiteDifferentialEntry,
    site_entry: PtmSiteEntry,
) -> tuple[PtmEvidenceCardWarning, ...]:
    warnings: list[PtmEvidenceCardWarning] = []
    if differential_entry.low_localization:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.LOW_LOCALIZATION,
                message="site differential remains low-localization and requires explicit review",
            )
        )
    if differential_entry.ambiguous:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.AMBIGUOUS_SITE,
                message="site evidence remains ambiguous across candidate positions",
            )
        )
    if differential_entry.shared_peptide:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.SHARED_PEPTIDE,
                message="site evidence is carried by a peptide shared across proteins",
            )
        )
    if site_entry.target_decoy_label is TargetDecoyLabel.DECOY:
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.DECOY_SITE,
                message="site evidence originates from decoy-labeled PTM support",
            )
        )
    if (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.MISSING_PROTEIN_BASELINE.value
    ):
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.MISSING_PROTEIN_BASELINE,
                message="protein-abundance correction could not be applied because matched protein evidence was missing",
            )
        )
    if (
        differential_entry.protein_correction_status
        == PtmProteinCorrectionStatus.CORRECTED_LOW_LOCALIZATION.value
    ):
        warnings.append(
            PtmEvidenceCardWarning(
                code=PtmEvidenceCardWarningCode.CORRECTED_LOW_LOCALIZATION,
                message="protein-abundance correction is present but remains review-only because localization is weak",
            )
        )
    return tuple(warnings)
