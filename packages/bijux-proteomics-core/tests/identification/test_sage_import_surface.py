# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.sage_import import (
    build_sage_import_report,
    render_sage_canonical_psm_tsv,
    render_sage_psm_tsv,
    render_sage_summary_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "sage"
    )


def test_sage_import_report_preserves_scores_modifications_and_q_values() -> None:
    root = _bundle_root()

    report = build_sage_import_report(
        root / "sage_psm.tsv",
        config_path=root / "sage_search.json",
    )

    assert report.dialect_id == "sage-psm"
    assert report.summary.accepted_psm_count == 3
    assert report.summary.rejected_psm_count == 0
    assert report.summary.canonical_psm_count == 3
    assert report.summary.modified_psm_count == 2
    assert report.summary.q_value_psm_count == 3
    assert report.summary.hyperscore_psm_count == 3
    assert report.summary.multi_protein_psm_count == 1
    assert report.summary.target_psm_count == 2
    assert report.summary.decoy_psm_count == 1
    assert report.rejected_evidence_rows == ()
    assert report.parameter_report is not None
    assert report.parameter_report.enzyme == "trypsin"
    assert report.parameter_report.variable_modifications[0].site == "M"
    assert report.canonical_psms[0].record.run_id == "run01.mzML"
    assert report.canonical_psms[0].record.spectrum_id == "sage-real-1001"
    assert report.canonical_psms[1].record.protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert report.canonical_psms[1].record.charge == 3
    assert (
        report.canonical_psms[1].record.modified_peptide
        == "AC[Carbamidomethyl]DM[Oxidation]K"
    )
    assert report.canonical_psms[1].hyperscore == 38.4
    assert report.psm_rows[0].residue_sequence == "PEPTIDE"
    assert report.psm_rows[0].modification_count == 1
    assert report.psm_rows[0].hyperscore == 41.2
    assert report.psm_rows[0].provenance.source_engine == "sage"
    assert report.psm_rows[0].provenance.source_row_numbers == (2,)
    assert report.psm_rows[1].protein_refs == (
        "sp|P23456|TRANSFER_HUMAN",
        "sp|P34567|TRANSFER_MOUSE",
    )
    assert report.psm_rows[1].matched_intensity_fraction == 0.541
    assert report.psm_rows[2].target_decoy_label.value == "decoy"

    assert "hyperscore_psm_count" in render_sage_summary_tsv(report.summary)
    assert "source_engine" in render_sage_canonical_psm_tsv(report.canonical_psms)
    assert "source_file" in render_sage_psm_tsv(report.psm_rows)


def test_sage_import_preserves_rejected_evidence_rows(tmp_path: Path) -> None:
    result_path = tmp_path / "sage_invalid.tsv"
    result_path.write_text(
        "\n".join(
            (
                "filename\tscannr\tpeptide\tcharge\tdiscriminant_score\thyperscore\tproteins\tlabel\tq_value\tpeptide_q_value\tprotein_q_value\tposterior_error\tmatched_peaks\tlongest_b\tlongest_y\tmatched_intensity_pct\tprecursor_ppm\tfragment_ppm\tisotope_error\trt\taligned_rt\tpredicted_rt\tdelta_rt_model",
                "run01.mzML\t1001\tPEP[+79.966331]TIDE\t2\t18.2\t41.2\tsp|P12345|KINASE_HUMAN\ttarget\t0.002\t0.002\t0.01\t0.001\t12\t4\t5\t0.61\t1.2\t0.01\t0\t600.0\t601.0\t602.0\t-1.0",
                "run01.mzML\t1002\tBROKEN\tbad\t11.4\t20.1\tsp|P23456|TRANSFER_HUMAN\ttarget\t0.01\t0.01\t0.02\t0.005\t9\t3\t4\t0.41\t2.2\t0.02\t0\t610.0\t611.0\t612.0\t-1.0",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_sage_import_report(result_path)

    assert report.summary.accepted_psm_count == 1
    assert report.summary.rejected_psm_count == 1
    assert len(report.rejected_evidence_rows) == 1
    assert report.rejected_evidence_rows[0].source_file == "sage_invalid.tsv"
    assert report.rejected_evidence_rows[0].entity_id == "1002"
    assert report.rejected_evidence_rows[0].reason_code == "invalid_charge"
