# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study import (
    build_experiment_design,
    build_experiment_design_validity_report,
    render_experiment_design_validity_tsv,
    require_valid_experiment_design_for_differential_analysis,
)


def _entry(
    *,
    sample_id: str,
    condition: str,
    spectra_file: str,
    replicate: int = 1,
    batch: str | None = None,
    pair_id: str | None = None,
    multiplex_group: str | None = None,
    multiplex_channel: str | None = None,
    sample_role: ExperimentalDesignSampleRole = ExperimentalDesignSampleRole.SAMPLE,
    metadata: dict[str, str] | None = None,
) -> ExperimentalDesignEntry:
    return ExperimentalDesignEntry(
        sample_id=sample_id,
        condition=condition,
        replicate=replicate,
        fraction=1,
        spectra_file=spectra_file,
        batch=batch,
        pair_id=pair_id,
        multiplex_group=multiplex_group,
        multiplex_channel=multiplex_channel,
        sample_role=sample_role,
        metadata=metadata or {},
    )


def test_design_validity_report_detects_conflicting_sample_identity_and_duplicate_run_ids() -> (
    None
):
    design = build_experiment_design(
        (
            _entry(sample_id="S1", condition="control", spectra_file="run-001"),
            _entry(sample_id="S1", condition="treatment", spectra_file="run-002"),
            _entry(sample_id="S2", condition="treatment", spectra_file="run-001"),
        )
    )

    report = build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.sample_identity_conflict_count == 1
    assert report.summary.duplicate_run_id_count == 1
    assert {issue.code for issue in report.issues} == {
        "conflicting_sample_identity",
        "duplicate_run_id",
    }
    assert "conflicting_sample_identity" in render_experiment_design_validity_tsv(
        report
    )


def test_design_validity_report_allows_consistent_multi_run_sample_ids() -> None:
    design = build_experiment_design(
        (
            _entry(sample_id="S1", condition="control", spectra_file="run-001"),
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-002",
                metadata={"timepoint": "T0"},
            ),
            _entry(
                sample_id="S2",
                condition="treatment",
                spectra_file="run-003",
                metadata={"timepoint": "T0"},
            ),
        )
    )

    report = build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.sample_identity_conflict_count == 0
    assert all(issue.code != "conflicting_sample_identity" for issue in report.issues)


def test_design_validity_report_detects_invalid_contrast_and_confounded_batches() -> (
    None
):
    design = build_experiment_design(
        (
            _entry(
                sample_id="C1",
                condition="control",
                spectra_file="run-c1",
                batch="batch-a",
            ),
            _entry(
                sample_id="C2",
                condition="control",
                spectra_file="run-c2",
                batch="batch-a",
            ),
            _entry(
                sample_id="T1",
                condition="treatment",
                spectra_file="run-t1",
                batch="batch-b",
            ),
            _entry(
                sample_id="T2",
                condition="treatment",
                spectra_file="run-t2",
                batch="batch-b",
            ),
        )
    )

    invalid_contrast = build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="missing",
    )
    confounded = build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="treatment",
        batch_field="batch",
    )

    assert invalid_contrast.summary.invalid_contrast_count == 1
    assert invalid_contrast.issues[0].code == "invalid_contrast_unknown_condition"
    assert confounded.summary.confounded_batch_condition_count == 1
    assert confounded.issues[0].code == "confounded_batch_condition"


def test_design_validity_report_detects_broken_pairs() -> None:
    design = build_experiment_design(
        (
            _entry(
                sample_id="C1",
                condition="control",
                spectra_file="run-c1",
                pair_id="pair-1",
            ),
            _entry(
                sample_id="T1",
                condition="treatment",
                spectra_file="run-t1",
                pair_id="pair-1",
            ),
            _entry(
                sample_id="C2",
                condition="control",
                spectra_file="run-c2",
                pair_id="pair-2",
            ),
            _entry(
                sample_id="T2",
                condition="treatment",
                spectra_file="run-t2",
                pair_id=None,
            ),
        )
    )

    report = build_experiment_design_validity_report(
        design,
        condition_a="control",
        condition_b="treatment",
        pairing_field="pair_id",
    )

    assert report.summary.broken_pair_count == 2
    assert all(issue.code == "broken_pair" for issue in report.issues)


def test_design_validity_report_detects_missing_multiplex_channels_and_timepoint_order() -> (
    None
):
    multiplex_design = build_experiment_design(
        (
            _entry(
                sample_id="plex-a-126",
                condition="control",
                spectra_file="plex-a-raw",
                multiplex_group="plex-a",
                multiplex_channel="126",
            ),
            _entry(
                sample_id="plex-a-127",
                condition="treatment",
                spectra_file="plex-a-raw",
                multiplex_group="plex-a",
                multiplex_channel="127N",
            ),
            _entry(
                sample_id="plex-b-126",
                condition="control",
                spectra_file="plex-b-raw",
                multiplex_group="plex-b",
                multiplex_channel="126",
            ),
        )
    )
    timepoint_design = build_experiment_design(
        (
            _entry(
                sample_id="S1",
                condition="control",
                spectra_file="run-001",
                metadata={"timepoint": "baseline"},
            ),
            _entry(
                sample_id="S2",
                condition="treatment",
                spectra_file="run-002",
                metadata={"timepoint": "endpoint"},
            ),
        )
    )

    multiplex_report = build_experiment_design_validity_report(
        multiplex_design,
        require_complete_plex_channels=True,
    )
    timepoint_report = build_experiment_design_validity_report(
        timepoint_design,
        timepoint_field="timepoint",
    )

    assert multiplex_report.summary.missing_channel_count == 1
    assert {issue.code for issue in multiplex_report.issues} == {
        "missing_multiplex_channels"
    }
    assert multiplex_report.issues[0].channel_ids == ("127N",)
    assert timepoint_report.summary.missing_timepoint_order_count == 1
    assert timepoint_report.issues[0].code == "missing_timepoint_order"


def test_require_valid_experiment_design_blocks_invalid_differential_metadata() -> None:
    design = build_experiment_design(
        (
            _entry(sample_id="S1", condition="control", spectra_file="run-001"),
            _entry(sample_id="S1", condition="treatment", spectra_file="run-002"),
        )
    )

    try:
        require_valid_experiment_design_for_differential_analysis(
            design,
            condition_a="control",
            condition_b="treatment",
        )
    except ValueError as exc:
        assert "experiment design is invalid for differential analysis" in str(exc)
        assert "conflicting_sample_identity" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected invalid experiment design to be rejected")
