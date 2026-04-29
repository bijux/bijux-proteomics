# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import parse_experimental_design_table
from bijux_proteomics_lab import (
    CarryoverRiskLevel,
    ContrastRejectionReason,
    InstrumentMethodMetadata,
    MultiplexChannelRole,
    SamplePreparationMetadata,
    assess_carryover_risk,
    build_fractionation_plan,
    build_lab_protocol_evidence_bundle,
    build_power_analysis_advisory,
    plan_batch_randomization,
    plan_multiplex_labeling,
    plan_spike_in_qc_samples,
    validate_experiment_design,
)


def _repo_packages_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _core_fixture(package: str, name: str) -> Path:
    return (
        _repo_packages_dir()
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / package
        / name
    )


def _local_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "design" / name


def test_validate_experiment_design_distinguishes_valid_and_confounded_contrasts() -> (
    None
):
    valid_entries = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    ).accepted_entries
    confounded_entries = parse_experimental_design_table(
        _local_fixture("confounded.design.tsv")
    ).accepted_entries

    valid_report = validate_experiment_design(valid_entries)
    confounded_report = validate_experiment_design(confounded_entries)

    assert len(valid_report.valid_contrasts) == 1
    assert valid_report.valid_contrasts[0].condition_a == "control"
    assert valid_report.valid_contrasts[0].condition_b == "treatment"
    assert len(confounded_report.rejected_contrasts) == 1
    assert (
        ContrastRejectionReason.BATCH_CONFOUNDED
        in confounded_report.rejected_contrasts[0].rejection_reasons
    )
    assert any(
        issue.code == "contrast-batch_confounded" for issue in confounded_report.issues
    )


def test_validate_experiment_design_exposes_structure_summary() -> None:
    valid_entries = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    ).accepted_entries
    fractionated_entries = parse_experimental_design_table(
        _local_fixture("fractionated.design.tsv")
    ).accepted_entries
    multiplex_entries = parse_experimental_design_table(
        _core_fixture("formats", "semantic.design.tsv")
    ).accepted_entries

    valid_report = validate_experiment_design(valid_entries)
    fractionated_report = validate_experiment_design(fractionated_entries)
    multiplex_report = validate_experiment_design(multiplex_entries, min_replicates=1)

    assert valid_report.structure_summary.replication.replicate_counts == {
        "control": 2,
        "treatment": 2,
    }
    assert valid_report.structure_summary.replication.balanced is True
    assert valid_report.structure_summary.control_like_condition_count == 1
    assert valid_report.structure_summary.fractionated is False
    assert valid_report.structure_summary.multiplexed is False

    assert fractionated_report.structure_summary.fractionated is True
    assert fractionated_report.structure_summary.maximum_fraction_count == 2
    assert fractionated_report.structure_summary.replication.minimum_replicates == 1

    assert multiplex_report.structure_summary.multiplexed is True
    assert multiplex_report.structure_summary.multiplex_group_count == 1
    assert multiplex_report.structure_summary.multiplex_channel_count == 3
    assert multiplex_report.structure_summary.pooled_reference_count == 1


def test_validate_experiment_design_warns_on_missing_control_and_asymmetric_replication() -> (
    None
):
    entries = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    ).accepted_entries
    advisory_entries = (
        entries[1].model_copy(update={"condition": "condition-a"}),
        entries[2].model_copy(update={"condition": "condition-b"}),
        entries[3].model_copy(update={"condition": "condition-b"}),
    )

    report = validate_experiment_design(advisory_entries, min_replicates=1)
    issue_codes = {issue.code for issue in report.issues}

    assert report.structure_summary.control_like_condition_count == 0
    assert report.structure_summary.replication.balanced is False
    assert "control-strategy-missing" in issue_codes
    assert "replication-strategy-asymmetric" in issue_codes


def test_build_power_analysis_advisory_exposes_current_and_recommended_replication() -> (
    None
):
    entries = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    ).accepted_entries

    advisory = build_power_analysis_advisory(
        entries,
        condition_a="control",
        condition_b="treatment",
        standardized_effect_size=1.0,
    )

    assert advisory.current_replicates == {"control": 2, "treatment": 2}
    assert advisory.recommended_replicates_per_condition >= 2
    assert advisory.estimated_power < advisory.target_power


def test_plan_batch_randomization_is_deterministic_and_condition_balanced() -> None:
    entries = parse_experimental_design_table(
        _local_fixture("multiplex.design.tsv")
    ).accepted_entries

    first = plan_batch_randomization(entries, seed=17)
    second = plan_batch_randomization(entries, seed=17)
    conditions = [slot.condition for slot in first.slots]

    assert first == second
    assert first.slot_count == 6
    assert first.condition_counts == {"control": 3, "treatment": 3}
    assert conditions[:4] == ["treatment", "control", "treatment", "control"]


def test_build_fractionation_plan_links_samples_fractions_and_run_labels() -> None:
    entries = parse_experimental_design_table(
        _local_fixture("fractionated.design.tsv")
    ).accepted_entries

    plan = build_fractionation_plan(entries)

    assert plan.sample_count == 2
    assert plan.total_fraction_count == 4
    assert [assignment.run_label for assignment in plan.assignments] == [
        "C1-f01",
        "C1-f02",
        "T1-f01",
        "T1-f02",
    ]


def test_plan_multiplex_labeling_reserves_reference_and_qc_channels() -> None:
    entries = parse_experimental_design_table(
        _local_fixture("multiplex.design.tsv")
    ).accepted_entries

    plan = plan_multiplex_labeling(
        entries,
        channels=("126", "127N", "127C", "128N", "128C", "129N", "129C", "130N"),
        pooled_reference_channel="126",
        qc_bridge_channel="130N",
    )

    assignments = {assignment.channel: assignment for assignment in plan.assignments}

    assert plan.balanced is True
    assert assignments["126"].role is MultiplexChannelRole.POOLED_REFERENCE
    assert assignments["130N"].role is MultiplexChannelRole.QC_BRIDGE
    assert plan.condition_channel_counts == {"control": 3, "treatment": 3}


def test_plan_multiplex_labeling_preserves_explicit_design_channel_semantics() -> None:
    entries = parse_experimental_design_table(
        _core_fixture("formats", "semantic.design.tsv")
    ).accepted_entries

    plan = plan_multiplex_labeling(
        entries,
        channels=("126", "127N", "128N"),
        pooled_reference_channel="128N",
    )

    assignments = {assignment.channel: assignment for assignment in plan.assignments}

    assert assignments["126"].sample_id == "CTRL-01"
    assert assignments["127N"].sample_id == "TRT-01"
    assert assignments["128N"].role is MultiplexChannelRole.POOLED_REFERENCE


def test_plan_multiplex_labeling_rejects_conflicting_reserved_channel_hints() -> None:
    entries = parse_experimental_design_table(
        _core_fixture("formats", "semantic.design.tsv")
    ).accepted_entries

    try:
        plan_multiplex_labeling(
            entries,
            channels=("126", "127N", "128N"),
            pooled_reference_channel="126",
        )
    except ValueError as exc:
        assert "explicit pooled_reference row" in str(exc)
    else:
        raise AssertionError("expected explicit pooled-reference conflict to fail")


def test_plan_spike_in_qc_samples_inserts_qc_and_spike_in_at_intervals() -> None:
    plan = plan_spike_in_qc_samples(
        ("C1", "C2", "T1", "T2", "T3"),
        qc_sample_id="QC-POOL",
        every_n_runs=2,
        spike_in_sample_id="SPIKE-STD",
    )

    assert plan.base_run_count == 5
    assert plan.expanded_run_order == (
        "C1",
        "C2",
        "QC-POOL",
        "SPIKE-STD",
        "T1",
        "T2",
        "QC-POOL",
        "SPIKE-STD",
        "T3",
    )
    assert [insertion.role for insertion in plan.insertions] == [
        "qc",
        "spike_in",
        "qc",
        "spike_in",
    ]


def test_assess_carryover_risk_flags_high_to_sensitive_transitions() -> None:
    advisory = assess_carryover_risk(
        ("blank-1", "mix-high", "sample-low", "blank-2"),
        abundance_tiers={
            "blank-1": "blank",
            "mix-high": "high",
            "sample-low": "low",
            "blank-2": "blank",
        },
    )

    assert len(advisory.flagged_transitions) == 2
    assert advisory.flagged_transitions[0].risk_level is CarryoverRiskLevel.HIGH
    assert advisory.flagged_transitions[1].following_tier == "blank"


def test_build_lab_protocol_evidence_bundle_collects_protocol_context() -> None:
    entries = parse_experimental_design_table(
        _local_fixture("fractionated.design.tsv")
    ).accepted_entries
    validation = validate_experiment_design(entries, min_replicates=1)
    randomization = plan_batch_randomization(entries, seed=5)
    fractionation = build_fractionation_plan(entries)
    qc_plan = plan_spike_in_qc_samples(
        tuple(slot.sample_id for slot in randomization.slots),
        qc_sample_id="QC-POOL",
        every_n_runs=2,
    )
    carryover = assess_carryover_risk(
        tuple(qc_plan.expanded_run_order),
        abundance_tiers=dict.fromkeys(qc_plan.expanded_run_order, "medium"),
    )

    bundle = build_lab_protocol_evidence_bundle(
        bundle_id="protocol-bundle-1",
        sample_preparation=SamplePreparationMetadata(
            protocol_id="prep-1",
            digestion_protocol="trypsin overnight",
            cleanup_method="stage-tip desalting",
            fractionation_strategy="high-pH reversed phase",
            labeling_strategy="label free",
            operator="lab-a",
        ),
        instrument_method=InstrumentMethodMetadata(
            method_id="orbitrap-dda-01",
            instrument="orbitrap",
            acquisition_mode="DDA",
            gradient_minutes=120.0,
            ms1_resolution=60000,
            ms2_resolution=15000,
            collision_energy=28.0,
        ),
        design_validation=validation,
        randomization_plan=randomization,
        fractionation_plan=fractionation,
        qc_plan=qc_plan,
        carryover_advisory=carryover,
    )

    assert bundle.bundle_id == "protocol-bundle-1"
    assert bundle.document_schema.created_by == "bijux-proteomics-lab"
    assert bundle.sample_preparation.fractionation_strategy == "high-pH reversed phase"
    assert bundle.instrument_method.acquisition_mode == "DDA"
    assert bundle.qc_plan is not None
