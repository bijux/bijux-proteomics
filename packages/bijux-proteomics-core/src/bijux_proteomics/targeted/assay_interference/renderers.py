# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""TSV renderers for targeted assay interference outputs."""

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.targeted.assay_interference.models import (
    TargetedAssayInterferenceReport,
)


def render_targeted_assay_interference_summary_tsv(
    report: TargetedAssayInterferenceReport,
) -> str:
    """Render compact targeted assay interference summary accounting as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("protease", report.protease))
    writer.writerow(("missed_cleavages", report.missed_cleavages))
    writer.writerow(("precursor_tolerance_da", f"{report.precursor_tolerance_da:.6f}"))
    writer.writerow(("fragment_tolerance_da", f"{report.fragment_tolerance_da:.6f}"))
    writer.writerow(
        ("coelution_rt_window_minutes", f"{report.coelution_rt_window_minutes:.6f}")
    )
    writer.writerow(("minimum_export_transitions", report.minimum_export_transitions))
    writer.writerow(("assay_entry_count", report.summary.assay_entry_count))
    writer.writerow(("low_risk_assay_count", report.summary.low_risk_assay_count))
    writer.writerow(("medium_risk_assay_count", report.summary.medium_risk_assay_count))
    writer.writerow(("high_risk_assay_count", report.summary.high_risk_assay_count))
    writer.writerow(("downgraded_assay_count", report.summary.downgraded_assay_count))
    writer.writerow(
        ("panel_export_assay_count", report.summary.panel_export_assay_count)
    )
    writer.writerow(("transition_entry_count", report.summary.transition_entry_count))
    writer.writerow(
        ("panel_export_transition_count", report.summary.panel_export_transition_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_targeted_assay_interference_assay_tsv(
    report: TargetedAssayInterferenceReport,
) -> str:
    """Render assay-level targeted interference scoring rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "peptide_rank",
            "precursor_charge",
            "precursor_mz",
            "selected_transition_count",
            "exported_transition_count",
            "shared_peptide_penalty",
            "panel_overlap_transition_count",
            "background_overlap_peptide_count",
            "library_overlap_peptide_count",
            "coeluting_library_overlap_peptide_count",
            "intrinsic_transition_risk_score",
            "interference_risk_score",
            "interference_risk_tier",
            "downgrade_reasons",
            "panel_export_allowed",
            "panel_export_caveat",
            "source_library_entry_id",
        )
    )
    for entry in report.assay_entries:
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.peptide_rank,
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                entry.selected_transition_count,
                entry.exported_transition_count,
                f"{entry.shared_peptide_penalty:.6f}",
                entry.panel_overlap_transition_count,
                entry.background_overlap_peptide_count,
                entry.library_overlap_peptide_count,
                entry.coeluting_library_overlap_peptide_count,
                f"{entry.intrinsic_transition_risk_score:.6f}",
                f"{entry.interference_risk_score:.6f}",
                entry.interference_risk_tier.value,
                ";".join(reason.value for reason in entry.downgrade_reasons),
                str(entry.panel_export_allowed).lower(),
                entry.panel_export_caveat,
                ""
                if entry.source_library_entry_id is None
                else entry.source_library_entry_id,
            )
        )
    return handle.getvalue()


def render_targeted_assay_interference_transition_tsv(
    report: TargetedAssayInterferenceReport,
) -> str:
    """Render transition-level targeted interference scoring rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "precursor_mz",
            "fragment_label",
            "ion_type",
            "fragment_ordinal",
            "fragment_charge",
            "fragment_sequence",
            "fragment_mz",
            "expected_relative_intensity",
            "selected_transition_rank",
            "intrinsic_interference_risk_score",
            "panel_overlap_transition_count",
            "background_overlap_peptide_count",
            "library_overlap_peptide_count",
            "coeluting_library_overlap_peptide_count",
            "interference_risk_score",
            "interference_risk_tier",
            "downgrade_reasons",
            "export_allowed",
            "export_caveat",
        )
    )
    for entry in report.transition_entries:
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                entry.fragment_label,
                entry.ion_type.value,
                entry.fragment_ordinal,
                entry.fragment_charge,
                entry.fragment_sequence,
                f"{entry.fragment_mz:.6f}",
                ""
                if entry.expected_relative_intensity is None
                else f"{entry.expected_relative_intensity:.6f}",
                entry.selected_transition_rank,
                f"{entry.intrinsic_interference_risk_score:.6f}",
                entry.panel_overlap_transition_count,
                entry.background_overlap_peptide_count,
                entry.library_overlap_peptide_count,
                entry.coeluting_library_overlap_peptide_count,
                f"{entry.interference_risk_score:.6f}",
                entry.interference_risk_tier.value,
                ";".join(reason.value for reason in entry.downgrade_reasons),
                str(entry.export_allowed).lower(),
                entry.export_caveat,
            )
        )
    return handle.getvalue()


def render_targeted_assay_interference_panel_tsv(
    report: TargetedAssayInterferenceReport,
) -> str:
    """Render the downgraded pre-run panel export after interference scoring."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "assay_entry_id",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "precursor_mz",
            "fragment_label",
            "fragment_mz",
            "expected_relative_intensity",
            "assay_interference_risk_tier",
            "transition_interference_risk_tier",
            "export_caveat",
        )
    )
    for entry in report.panel_entries:
        writer.writerow(
            (
                entry.assay_entry_id,
                entry.target_protein_ref,
                entry.target_protein_group_id,
                "" if entry.gene_symbol is None else entry.gene_symbol,
                entry.peptide_sequence,
                entry.canonical_peptide,
                entry.precursor_charge,
                f"{entry.precursor_mz:.6f}",
                entry.fragment_label,
                f"{entry.fragment_mz:.6f}",
                ""
                if entry.expected_relative_intensity is None
                else f"{entry.expected_relative_intensity:.6f}",
                entry.assay_interference_risk_tier.value,
                entry.transition_interference_risk_tier.value,
                entry.export_caveat,
            )
        )
    return handle.getvalue()


__all__ = [
    "render_targeted_assay_interference_assay_tsv",
    "render_targeted_assay_interference_panel_tsv",
    "render_targeted_assay_interference_summary_tsv",
    "render_targeted_assay_interference_transition_tsv",
]
