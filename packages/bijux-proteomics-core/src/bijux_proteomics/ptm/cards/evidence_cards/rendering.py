# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV rendering and export support for PTM evidence cards."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.card_schema import (
    StandardCardEntry,
    StandardCardKind,
    StandardCardSubjectKind,
    render_standard_card_row,
)
from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.ptm.cards.evidence_cards.models import (
    PtmEvidenceCard,
    PtmEvidenceCardReport,
)
from bijux_proteomics.ptm.localization_scoring import PtmLocalizationConfidenceTier


def render_ptm_evidence_card_summary_tsv(report: PtmEvidenceCardReport) -> str:
    """Render a compact PTM evidence-card summary as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "condition_a",
            "condition_b",
            "significant_site_count",
            "card_count",
            "narrative_claim_count",
            "regulator_supported_card_count",
            "motif_annotated_card_count",
            "crosstalk_supported_card_count",
            "mechanism_classified_card_count",
            "ortholog_context_card_count",
            "functional_context_card_count",
            "warning_card_count",
        )
    )
    writer.writerow(
        (
            report.condition_a,
            report.condition_b,
            report.summary.significant_site_count,
            report.summary.card_count,
            report.summary.narrative_claim_count,
            report.summary.regulator_supported_card_count,
            report.summary.motif_annotated_card_count,
            report.summary.crosstalk_supported_card_count,
            report.summary.mechanism_classified_card_count,
            report.summary.ortholog_context_card_count,
            report.summary.functional_context_card_count,
            report.summary.warning_card_count,
        )
    )
    return buffer.getvalue()


def render_ptm_evidence_card_tsv(report: PtmEvidenceCardReport) -> str:
    """Render PTM evidence cards as a flat TSV ledger."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
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
            "site_key",
            "protein_ref",
            "residue",
            "position",
            "modification_name",
            "target_decoy_label",
            "identity_level",
            "identity_reason",
            "condition_a",
            "condition_b",
            "adjusted_p_value",
            "log2_fold_change",
            "corrected_log2_fold_change",
            "localization_tier",
            "protein_correction_status",
            "mechanism_class",
            "mechanism_reason_codes",
            "peptide_spectrum_count",
            "observed_sample_count",
            "centered_windows",
            "ortholog_conservation_status",
            "ortholog_conservation_species_pair",
            "ortholog_target_site_keys",
            "ortholog_target_protein_refs",
            "functional_regions",
            "regulators",
            "crosstalk_partner_site_keys",
            "crosstalk_relationships",
            "crosstalk_evidence_sources",
            "crosstalk_shared_pathways",
            "claim_ids",
            "source_row_refs",
            "derived_no_source_reason",
        )
    )
    for entry in report.cards:
        standard_card = _build_standard_card_entry(entry)
        writer.writerow(
            (
                *render_standard_card_row(standard_card),
                entry.site_key,
                entry.protein_ref,
                entry.residue,
                entry.position,
                entry.modification_name,
                entry.target_decoy_label.value,
                entry.identity_level.value,
                entry.identity_reason,
                entry.differential_result.condition_a,
                entry.differential_result.condition_b,
                ""
                if entry.differential_result.adjusted_p_value is None
                else entry.differential_result.adjusted_p_value,
                entry.differential_result.log2_fold_change,
                (
                    ""
                    if entry.protein_correction.corrected_log2_fold_change is None
                    else entry.protein_correction.corrected_log2_fold_change
                ),
                entry.localization.localization_tier.value,
                entry.protein_correction.status,
                (
                    ""
                    if entry.mechanism_classification is None
                    else entry.mechanism_classification.mechanism_class.value
                ),
                (
                    ""
                    if entry.mechanism_classification is None
                    else ";".join(
                        reason.value
                        for reason in entry.mechanism_classification.reason_codes
                    )
                ),
                len(entry.peptide_evidence),
                0
                if entry.quantification is None
                else entry.quantification.observed_sample_count,
                ";".join(entry.motif_evidence.centered_windows),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else entry.ortholog_conservation.status.value
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else (
                        f"{entry.ortholog_conservation.source_species}->"
                        f"{entry.ortholog_conservation.target_species}"
                    )
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else ";".join(entry.ortholog_conservation.ortholog_target_site_keys)
                ),
                (
                    ""
                    if entry.ortholog_conservation is None
                    else ";".join(
                        entry.ortholog_conservation.ortholog_target_protein_refs
                    )
                ),
                ";".join(
                    f"{region.region_kind.value}:{region.label}@{region.start}-{region.end}"
                    for region in entry.functional_regions
                ),
                ";".join(
                    f"{regulator.regulator}:{regulator.direction}"
                    for regulator in entry.regulator_evidence
                ),
                ";".join(
                    partner.partner_site_key for partner in entry.crosstalk_partners
                ),
                ";".join(
                    partner.relationship.value for partner in entry.crosstalk_partners
                ),
                ";".join(
                    ",".join(source.value for source in partner.evidence_sources)
                    for partner in entry.crosstalk_partners
                ),
                ";".join(
                    ",".join(partner.shared_pathways)
                    for partner in entry.crosstalk_partners
                    if partner.shared_pathways
                ),
                ";".join(entry.claim_ids),
                ";".join(entry.source_row_refs),
                ""
                if entry.derived_no_source_reason is None
                else entry.derived_no_source_reason,
            )
        )
    return buffer.getvalue()


def render_ptm_evidence_claim_tsv(report: PtmEvidenceCardReport) -> str:
    """Render PTM evidence-card narrative claims as TSV."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "claim_id",
            "card_id",
            "site_key",
            "claim_kind",
            "text",
            "source_row_refs",
            "derived_no_source_reason",
        )
    )
    for entry in report.narrative_claims:
        writer.writerow(
            (
                entry.claim_id,
                entry.card_id,
                entry.site_key,
                entry.claim_kind.value,
                entry.text,
                ";".join(entry.source_row_refs),
                ""
                if entry.derived_no_source_reason is None
                else entry.derived_no_source_reason,
            )
        )
    return buffer.getvalue()


def export_ptm_evidence_card_summary_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence-card summary to a stable TSV artifact."""
    write_output_table_tsv(path, render_ptm_evidence_card_summary_tsv(report))


def export_ptm_evidence_card_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence cards to a stable TSV artifact."""
    write_output_table_tsv(path, render_ptm_evidence_card_tsv(report))


def export_ptm_evidence_claim_tsv(
    report: PtmEvidenceCardReport,
    path: Path,
) -> None:
    """Write PTM evidence-card narrative claims to a stable TSV artifact."""
    write_output_table_tsv(path, render_ptm_evidence_claim_tsv(report))


def _build_standard_card_entry(entry: PtmEvidenceCard) -> StandardCardEntry:
    return StandardCardEntry(
        card_id=entry.card_id,
        card_kind=StandardCardKind.PTM,
        subject_kind=StandardCardSubjectKind.PTM_SITE,
        subject_id=entry.site_key,
        subject_label=(
            f"{entry.protein_ref} {entry.residue}{entry.position} {entry.modification_name}"
        ),
        claim=(
            f"PTM site {entry.site_key} has log2 fold change "
            f"{entry.differential_result.log2_fold_change:g} between "
            f"{entry.differential_result.condition_a} and {entry.differential_result.condition_b}."
        ),
        evidence_for=(
            f"localization tier is {entry.localization.localization_tier.value}; "
            f"{len(entry.peptide_evidence)} peptide-spectrum matches support this site."
        ),
        evidence_against=(
            "no explicit weakening evidence was preserved on this PTM card."
            if not entry.warnings
            else "warnings remained attached: "
            + ", ".join(warning.code.value for warning in entry.warnings)
            + "."
        ),
        confidence=_standard_card_confidence(entry.localization.localization_tier),
        warning_codes=tuple(warning.code.value for warning in entry.warnings),
        source_ids=tuple(dict.fromkeys((*entry.source_row_refs, *entry.claim_ids))),
    )


def _standard_card_confidence(
    localization_tier: PtmLocalizationConfidenceTier,
) -> ConfidenceTier:
    if localization_tier is PtmLocalizationConfidenceTier.HIGH_CONFIDENCE:
        return ConfidenceTier.HIGH
    if localization_tier is PtmLocalizationConfidenceTier.SUPPORTED:
        return ConfidenceTier.MODERATE
    return ConfidenceTier.LOW
