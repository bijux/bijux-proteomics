# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.score_separation_diagnostic import (
    ScoreSeparationWarningTier,
    build_score_separation_diagnostic_report,
    render_score_separation_bins_tsv,
    render_score_separation_summary_tsv,
)


def _record(
    spectrum_id: str,
    peptide: str,
    score: float,
    label: TargetDecoyLabel,
) -> PsmRecord:
    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=peptide,
        charge=2,
        score=score,
        protein_refs=("P11111",)
        if label is TargetDecoyLabel.TARGET
        else ("DECOY_P99999",),
        target_decoy_label=label,
    )


def test_score_separation_report_flags_missing_decoys_as_unstable() -> None:
    report = build_score_separation_diagnostic_report(
        (
            _record("all-target-001", "PEPA", 100.0, TargetDecoyLabel.TARGET),
            _record("all-target-002", "PEPB", 95.0, TargetDecoyLabel.TARGET),
        )
    )

    assert report.summary.target_dominance_fraction is None
    assert report.summary.overlap_metric == 1.0
    assert report.summary.warning_tier is ScoreSeparationWarningTier.UNSTABLE
    assert report.summary.fdr_unstable is True
    assert report.summary.note.startswith(
        "target-decoy score separation is unavailable"
    )


def test_score_separation_renderers_emit_bins_and_summary_ledgers() -> None:
    report = build_score_separation_diagnostic_report(
        (
            _record("rank-001", "PEPA", 100.0, TargetDecoyLabel.TARGET),
            _record("rank-002", "DECA", 95.0, TargetDecoyLabel.DECOY),
            _record("rank-003", "PEPB", 90.0, TargetDecoyLabel.TARGET),
            _record("rank-004", "DECB", 85.0, TargetDecoyLabel.DECOY),
        ),
        bin_count=4,
    )

    summary_tsv = render_score_separation_summary_tsv(report)
    bins_tsv = render_score_separation_bins_tsv(report)

    assert report.reproducibility_hash
    assert summary_tsv.startswith(
        "score_orientation\tbin_count\twarning_overlap_threshold"
    )
    assert "\t0.75\tunstable\ttrue\t" in summary_tsv
    assert bins_tsv.startswith(
        "bin_lower\tbin_upper\ttarget_count\tdecoy_count\tmixed_count\tunknown_count"
    )
    assert "0.25\t0.5\t1\t0\t0\t0\t0.5\t0.0\t0.0" in bins_tsv
