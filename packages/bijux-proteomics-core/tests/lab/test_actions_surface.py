# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.lab import (
    BackgroundComparisonEntry,
    CohortBalanceEntry,
    ContaminantClass,
    ContaminationClassificationEntry,
    DigestionDiagnosisEntry,
    DigestionStatus,
    InternalStandardTrackingEntry,
    LabActionPacket,
    LabQcStatus,
    RunDiagnosisEntry,
    RunFailureClass,
    SampleSwapSuspicionEntry,
    build_lab_action_packets,
    build_lab_action_packets_from_qc_assessment,
    parse_lab_action_assessment_tsv,
    parse_lab_action_packet_tsv,
    render_lab_action_packets_tsv,
)


def test_build_lab_action_packets_ties_every_recommendation_to_specific_failure_rows() -> (
    None
):
    packets = build_lab_action_packets(
        (
            RunDiagnosisEntry(
                run_id="run-01",
                status=LabQcStatus.FAIL,
                failure_class=RunFailureClass.IDENTIFICATION_FAILURE,
                primary_reason="low_identification_yield",
                secondary_reasons=("weak_ms2_fragmentation",),
            ),
            DigestionDiagnosisEntry(
                sample_id="sample-digest",
                missed_cleavage_rate=0.31,
                semi_specific_rate=0.05,
                non_specific_rate=0.01,
                digestion_status=DigestionStatus.INEFFICIENT_DIGESTION,
            ),
            ContaminationClassificationEntry(
                sample_id="sample-contam",
                contaminant_class=ContaminantClass.KERATIN,
                top_contaminant_proteins=("KRT1", "KRT10"),
                intensity_fraction=0.12,
                action_hint="audit sample handling and exposed surfaces for skin or dust contamination",
            ),
            BackgroundComparisonEntry(
                entity_id="P001",
                sample_id="sample-bg",
                blank_intensity=1200.0,
                sample_intensity=1500.0,
                background_ratio=0.8,
                background_flag=True,
            ),
            InternalStandardTrackingEntry(
                standard_id="STD_A",
                sample_id="sample-std",
                intensity=0.0,
                cv=0.42,
                missing=True,
                drift_flag=True,
            ),
            SampleSwapSuspicionEntry(
                sample_id="sample-swap",
                expected_group="case",
                nearest_neighbor_sample="control-2",
                nearest_neighbor_group="control",
                swap_suspicion_score=0.97,
            ),
            CohortBalanceEntry(
                covariate="sex",
                group_counts="female[case=0,control=2];male[case=2,control=0]",
                imbalance_score=1.0,
                confounded_with_condition=True,
                analysis_warning="covariate sex is fully confounded with condition and blocks naive subgroup interpretation",
            ),
            RunDiagnosisEntry(
                run_id="run-pass",
                status=LabQcStatus.PASSED,
                failure_class=RunFailureClass.NO_FAILURE,
                primary_reason="no_material_qc_failure_detected",
                secondary_reasons=(),
            ),
        )
    )

    lookup = {
        (packet.entity_type, packet.entity_id, packet.problem): packet
        for packet in packets
    }

    run_packet = lookup[("run", "run-01", "low_identification_yield")]
    assert run_packet.severity == "high"
    assert "run_id=run-01" in run_packet.evidence_rows
    assert "identification" in run_packet.recommended_action

    digestion_packet = lookup[("sample", "sample-digest", "inefficient_digestion")]
    assert "missed_cleavage_rate=0.3100" in digestion_packet.evidence_rows

    contamination_packet = lookup[("sample", "sample-contam", "keratin_contamination")]
    assert contamination_packet.severity == "high"
    assert "KRT1;KRT10" in contamination_packet.evidence_rows[2]

    background_packet = lookup[
        ("sample_entity", "sample-bg:P001", "blank_dominated_background")
    ]
    assert "background_ratio=0.8000" in background_packet.evidence_rows

    internal_standard_packet = lookup[
        ("standard_sample", "sample-std:STD_A", "internal_standard_missing")
    ]
    assert internal_standard_packet.severity == "high"
    assert "missing=true" in internal_standard_packet.evidence_rows

    sample_swap_packet = lookup[("sample", "sample-swap", "sample_swap_suspicion")]
    assert "do not relabel automatically" in sample_swap_packet.recommended_action

    cohort_packet = lookup[("covariate", "sex", "condition_confounded_covariate")]
    assert "blocks naive subgroup interpretation" in cohort_packet.recommended_action

    assert all(packet.entity_id != "run-pass" for packet in packets)


def test_render_lab_action_packets_tsv_is_stable() -> None:
    packets = (
        LabActionPacket(
            entity_type="run",
            entity_id="run-01",
            problem="low_identification_yield",
            evidence_rows=("run_id=run-01", "failure_class=identification_failure"),
            recommended_action="review precursor isolation, fragmentation yield, and search-ready identification depth for this run",
            severity="high",
        ),
    )

    rendered = render_lab_action_packets_tsv(packets)

    assert rendered.startswith(
        "entity_type\tentity_id\tproblem\tevidence_rows\trecommended_action\tseverity\n"
    )
    assert "run\trun-01\tlow_identification_yield\t" in rendered


def test_build_lab_action_packets_from_qc_assessment_preserves_failed_run_handoff(
    tmp_path: Path,
) -> None:
    assessment_path = tmp_path / "run_qc.tsv"
    assessment_path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tseverity\tdisposition\tenforced_violation\tmessage",
                "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
                "sample\tT2\tcaution\tmissing_internal_standard\tinternal_standard\twarning\treview\tfalse\tinternal standard drift exceeded acceptance policy",
                "run\tpass-run\tpass\t\tidentification_rate\tok\taccept\tfalse\tpass",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    entries = parse_lab_action_assessment_tsv(assessment_path)
    packets = build_lab_action_packets_from_qc_assessment(entries)

    assert len(entries) == 3
    assert [packet.entity_id for packet in packets] == ["t2.mzml", "T2"]
    run_packet = next(packet for packet in packets if packet.entity_id == "t2.mzml")
    sample_packet = next(packet for packet in packets if packet.entity_id == "T2")

    assert run_packet.problem == "identification_rate_low"
    assert run_packet.severity == "high"
    assert "metric_key=identification_rate" in run_packet.evidence_rows
    assert "identification depth" in run_packet.recommended_action
    assert sample_packet.problem == "missing_internal_standard"
    assert sample_packet.severity == "medium"
    assert "sample-level interpretation" in sample_packet.recommended_action


def test_parse_lab_action_packet_tsv_round_trips_rendered_packets(
    tmp_path: Path,
) -> None:
    packets = (
        LabActionPacket(
            entity_type="run",
            entity_id="t2.mzml",
            problem="identification_rate_low",
            evidence_rows=("scope=run", "entity_id=t2.mzml"),
            recommended_action="review precursor isolation, fragmentation yield, and search-ready identification depth before accepting or rerunning this QC-failed run",
            severity="high",
        ),
    )
    path = tmp_path / "lab_action_packets.tsv"
    path.write_text(render_lab_action_packets_tsv(packets), encoding="utf-8")

    parsed = parse_lab_action_packet_tsv(path)

    assert parsed == packets
