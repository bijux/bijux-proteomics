# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.fragpipe_import import (
    build_fragpipe_import_report,
    render_fragpipe_canonical_psm_tsv,
    render_fragpipe_open_search_evidence_tsv,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_quantity_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
    render_fragpipe_summary_tsv,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    normalize_search_results_with_adapter,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "fragpipe"
    )


def test_fragpipe_import_report_preserves_bundle_tables_and_open_search_state() -> None:
    root = _bundle_root()

    report = build_fragpipe_import_report(
        root / "psm.tsv",
        peptide_tsv_path=root / "combined_peptide.tsv",
        protein_tsv_path=root / "combined_protein.tsv",
        quant_tsv_path=root / "combined_quant.tsv",
    )

    assert report.summary.accepted_psm_count == 3
    assert report.summary.rejected_psm_count == 0
    assert report.summary.peptide_row_count == 2
    assert report.summary.protein_row_count == 3
    assert report.summary.canonical_psm_count == 3
    assert report.summary.peptide_evidence_count == 2
    assert report.summary.protein_reference_count == 3
    assert report.summary.open_search_evidence_count == 2
    assert report.summary.protein_quantity_count == 6
    assert report.summary.modified_psm_count == 2
    assert report.summary.modified_peptide_row_count == 2
    assert report.summary.open_search_psm_count == 1
    assert report.summary.open_search_peptide_count == 1
    assert report.summary.q_value_psm_count == 3
    assert report.summary.q_value_peptide_count == 2
    assert report.summary.mapped_protein_count == 3
    assert report.summary.target_protein_count == 2
    assert report.summary.decoy_protein_count == 1
    assert report.canonical_psms[0].record.canonical_peptide == "PEPTIDE"
    assert report.canonical_psms[1].mass_difference == 42.0106
    assert report.canonical_psms[1].open_search_candidate is True
    assert report.psm_rows[0].canonical_modified_peptide == "PEP[+15.994915]TIDE"
    assert report.psm_rows[0].provenance.source_engine == "msfragger"
    assert report.psm_rows[0].provenance.source_row_numbers == (2,)
    assert report.psm_rows[1].open_search_candidate is True
    assert report.psm_rows[1].mass_difference == 42.0106
    assert report.peptide_evidence[1].open_search_candidate is True
    assert report.peptide_rows[0].provenance.source_engine == "fragpipe-peptide"
    assert report.peptide_rows[0].provenance.source_row_numbers == (2,)
    assert report.peptide_rows[1].mapped_protein_refs == ("sp|P34567|TRANSFER_MOUSE",)
    assert {row.entity_kind for row in report.open_search_evidence} == {"psm", "peptide"}
    assert {row.mass_difference for row in report.open_search_evidence} == {42.0106}
    assert report.protein_quantity_rows[0].quantity_kind == "maxlfq_intensity"
    assert report.protein_quantity_rows[0].provenance.source_engine == "fragpipe-quant"
    assert report.protein_quantity_rows[0].provenance.source_row_numbers
    assert any(
        row.target_decoy_label.value == "decoy" for row in report.protein_quantity_rows
    )
    assert report.protein_rows[0].provenance.source_engine == "fragpipe-protein"
    assert report.protein_rows[-1].target_decoy_label.value == "target"
    assert any(row.target_decoy_label.value == "decoy" for row in report.protein_rows)

    assert "accepted_psm_count" in render_fragpipe_summary_tsv(report.summary)
    assert "source_row_numbers" in render_fragpipe_canonical_psm_tsv(
        report.canonical_psms
    )
    assert "source_engine" in render_fragpipe_psm_tsv(report.psm_rows)
    assert "mapped_protein_refs" in render_fragpipe_peptide_tsv(report.peptide_rows)
    assert "source_row_numbers" in render_fragpipe_peptide_tsv(report.peptide_rows)
    assert "coverage_fraction" in render_fragpipe_protein_tsv(report.protein_rows)
    assert "original_identifiers" in render_fragpipe_protein_tsv(report.protein_rows)
    assert "mass_difference" in render_fragpipe_open_search_evidence_tsv(
        report.open_search_evidence
    )
    assert "source_file" in render_fragpipe_protein_quantity_tsv(
        report.protein_quantity_rows
    )


def test_fragpipe_psm_dialect_normalizes_realistic_psm_exports() -> None:
    report = normalize_search_results_with_adapter(
        source_path=_bundle_root() / "psm.tsv",
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
    )

    assert report.adapter_manifest.display_name == "FragPipe psm export"
    assert report.normalized_records[0].canonical_peptide == "PEPTIDE"
    assert report.normalized_records[0].q_value == 0.002
    assert report.normalized_records[0].run_id == "runA.raw"
    assert report.normalized_records[0].intensity is None
    assert (
        report.evidence_rows[0].raw_fields["Modified Peptide"] == "PEP[+15.994915]TIDE"
    )
