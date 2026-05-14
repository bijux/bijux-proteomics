# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    build_psm_evidence_inspection_report,
    parse_psm_tsv,
    render_psm_evidence_inspection_summary_tsv,
    render_psm_inspection_distribution_tsv,
)


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_psm_evidence_inspection_report_covers_quality_distributions(
    tmp_path: Path,
) -> None:
    source = tmp_path / "psm_inspection.tsv"
    source.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins",
                "scan=1001\tPEPTIDE\t2\t55.0\t0.005\tP12345",
                "scan=1002\tAKTIDEK\t3\t44.0\t0.02\tP12345",
                "scan=1003\tLVVVVVVIKAKK\t2\t31.0\t0.08\tP12345",
                "scan=1004\tPEPTIDER\tbad\t20.0\t0.2\tP12345",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    parse_report = parse_psm_tsv(source, mapping=_default_mapping())
    report = build_psm_evidence_inspection_report(parse_report, protease="trypsin")

    assert report.total_rows == 4
    assert report.accepted_rows == 3
    assert report.rejected_rows == 1
    assert report.protease == "trypsin"
    assert {entry.bucket: entry.count for entry in report.score_distribution} == {
        "30-40": 1,
        "40-50": 1,
        "50-60": 1,
    }
    assert {entry.bucket: entry.count for entry in report.q_value_distribution} == {
        "0-0.01": 1,
        "0.01-0.05": 1,
        "0.05-0.1": 1,
    }
    assert {entry.bucket: entry.count for entry in report.charge_distribution} == {
        "2": 2,
        "3": 1,
    }
    assert {
        entry.bucket: entry.count for entry in report.peptide_length_distribution
    } == {"1-7": 2, "8-14": 1}
    assert {
        entry.bucket: entry.count for entry in report.missed_cleavage_distribution
    } == {"0": 1, "1": 1, "2": 1}


def test_psm_evidence_inspection_tsv_renderers_emit_review_ledgers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "psm_inspection.tsv"
    source.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins",
                "scan=2001\tPEPTIDE\t2\t42.0\t0.01\tP12345",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    parse_report = parse_psm_tsv(source, mapping=_default_mapping())
    report = build_psm_evidence_inspection_report(parse_report)

    summary_tsv = render_psm_evidence_inspection_summary_tsv(report)
    score_tsv = render_psm_inspection_distribution_tsv(report.score_distribution)

    assert "metric\tvalue" in summary_tsv
    assert "accepted_rows\t1" in summary_tsv
    assert "bucket\tcount" in score_tsv
    assert "40-50\t1" in score_tsv
