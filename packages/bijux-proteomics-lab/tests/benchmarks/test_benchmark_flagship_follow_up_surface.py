# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_lab.benchmarks import (
    FlagshipLabPacketPosture,
    build_flagship_assay_burden_report,
    build_flagship_lab_follow_up_packet,
    build_flagship_lab_follow_up_packet_family,
    build_flagship_lab_review_board,
    build_flagship_minimum_controls_table,
    build_flagship_not_worth_assay_report,
)


def test_flagship_lab_follow_up_packet_family_starts_with_reviewable_dda_and_dia() -> (
    None
):
    family = build_flagship_lab_follow_up_packet_family()

    assert family.family_id == "flagship-lab-follow-up-packets"
    assert family.artifact_path.startswith("artifacts/")
    assert [packet.workflow_family for packet in family.packets] == [
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    ]


def test_dda_follow_up_packet_keeps_controls_boundaries_and_tradeoffs_visible() -> None:
    packet = build_flagship_lab_follow_up_packet(KnowledgeWorkflowFamily.DDA)

    assert packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
    assert "pooled_reference" in packet.required_controls
    assert "digest_reproducibility_reference" in packet.required_controls
    assert any("target-decoy" in line for line in packet.decision_grade_boundary)
    assert any("contaminant" in line for line in packet.expected_failure_modes)
    assert packet.burden_profile.estimated_relative_cost > 0.0
    assert packet.burden_profile.estimated_queue_days >= 1
    assert packet.burden_profile.tradeoffs


def test_dia_follow_up_packet_marks_exploratory_and_decision_grade_boundaries() -> None:
    packet = build_flagship_lab_follow_up_packet(KnowledgeWorkflowFamily.DIA)

    assert packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
    assert "library_reference" in packet.required_controls
    assert "bridge_sample" in packet.required_controls
    assert any("exploratory" in line.lower() for line in packet.exploratory_boundary)
    assert any(
        "decision-grade" in line.lower() for line in packet.decision_grade_boundary
    )
    assert any("library" in line.lower() for line in packet.expected_failure_modes)


def test_lfq_packet_makes_replicate_and_design_weakness_visible() -> None:
    packet = build_flagship_lab_follow_up_packet(KnowledgeWorkflowFamily.LFQ)

    assert packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
    assert any("replicate" in line.lower() for line in packet.design_conditions)
    assert any("randomized" in line.lower() for line in packet.design_conditions)
    assert any("missingness" in line.lower() for line in packet.expected_failure_modes)
    assert any("extra sample" in line.lower() for line in packet.stop_reasons)


def test_ptm_packet_keeps_ambiguity_and_targetability_blockers_explicit() -> None:
    packet = build_flagship_lab_follow_up_packet(KnowledgeWorkflowFamily.PTM)

    assert packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
    assert "site_localization_reference" in packet.required_controls
    assert "unmodified_counterpart_control" in packet.required_controls
    assert any("ambiguity" in line.lower() for line in packet.expected_failure_modes)
    assert any("orthogonal" in line.lower() for line in packet.stop_reasons)


def test_targeted_packet_keeps_transition_calibration_and_interference_visible() -> (
    None
):
    packet = build_flagship_lab_follow_up_packet(KnowledgeWorkflowFamily.TARGETED)

    assert packet.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert packet.posture is FlagshipLabPacketPosture.EXPLORATORY_ONLY
    assert "heavy_reference" in packet.required_controls
    assert "calibration_standard" in packet.required_controls
    assert "interference_scout_injection" in packet.required_controls
    assert any("transition" in line.lower() for line in packet.design_conditions)
    assert any("interference" in line.lower() for line in packet.expected_failure_modes)


def test_flagship_assay_burden_report_ranks_high_burden_work_before_queueing() -> None:
    report = build_flagship_assay_burden_report()

    assert report.report_id == "flagship-assay-burden-report"
    assert report.artifact_path.startswith("artifacts/")
    assert report.entries[0].workflow_family is KnowledgeWorkflowFamily.PTM
    assert report.entries[0].queue_posture == "reserve_controlled_queue_slot"
    assert report.entries[-1].workflow_family is KnowledgeWorkflowFamily.DDA


def test_not_worth_assay_report_lists_interesting_but_blocked_workflows() -> None:
    report = build_flagship_not_worth_assay_report()

    assert report.report_id == "flagship-not-worth-assay-report"
    assert report.entries == ()


def test_flagship_minimum_controls_table_covers_every_workflow_family() -> None:
    table = build_flagship_minimum_controls_table()

    assert table.table_id == "flagship-minimum-controls-table"
    assert table.artifact_path.startswith("artifacts/")
    assert {entry.workflow_family for entry in table.entries} == {
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.MULTIPLEX,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    }
    multiplex_entry = next(
        entry
        for entry in table.entries
        if entry.workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
    )
    assert "reference_channel" in multiplex_entry.minimum_controls
    assert "bridge_channel" in multiplex_entry.minimum_controls
    assert multiplex_entry.current_blockers


def test_flagship_lab_review_board_ranks_by_science_and_operational_feasibility() -> (
    None
):
    artifact = build_flagship_lab_review_board()

    assert artifact.artifact_id == "flagship-lab-review-board"
    assert artifact.artifact_path.startswith("artifacts/")
    assert artifact.entries[0].workflow_family is KnowledgeWorkflowFamily.DDA
    assert artifact.entries[1].workflow_family is KnowledgeWorkflowFamily.LFQ
    assert artifact.entries[-1].workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
    assert (
        artifact.entries[0].overall_priority_score
        >= artifact.entries[-1].overall_priority_score
    )
    assert all(entry.rationale for entry in artifact.entries)
