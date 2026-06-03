# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.study import (
    ExperimentDesignAnalysisFamily,
    ExperimentDesignType,
    build_experiment_design,
    build_experiment_design_classification_report,
    render_experiment_design_classification_tsv,
    require_matching_experiment_design_analysis_family,
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


def test_design_classification_detects_two_group_and_paired_types() -> None:
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
                pair_id="pair-2",
            ),
        )
    )

    report = build_experiment_design_classification_report(design)

    assert report.primary_design_type is ExperimentDesignType.PAIRED
    assert report.detected_design_types == (
        ExperimentDesignType.TWO_GROUP,
        ExperimentDesignType.PAIRED,
    )
    assert (
        report.recommended_analysis_family
        is ExperimentDesignAnalysisFamily.PAIRED_DIFFERENTIAL
    )


def test_design_classification_detects_longitudinal_multi_group_and_tmt_layouts() -> (
    None
):
    design = build_experiment_design(
        (
            _entry(
                sample_id="plex-a-126",
                condition="control",
                spectra_file="plex-a.raw",
                replicate=1,
                multiplex_group="plex-a",
                multiplex_channel="126",
                metadata={"timepoint": "T0"},
            ),
            _entry(
                sample_id="plex-a-127N",
                condition="treatment",
                spectra_file="plex-a.raw",
                replicate=1,
                multiplex_group="plex-a",
                multiplex_channel="127N",
                metadata={"timepoint": "T0"},
            ),
            _entry(
                sample_id="plex-a-128N",
                condition="recovery",
                spectra_file="plex-a.raw",
                replicate=1,
                multiplex_group="plex-a",
                multiplex_channel="128N",
                metadata={"timepoint": "T1"},
            ),
        )
    )

    report = build_experiment_design_classification_report(
        design,
        timepoint_field="timepoint",
    )

    assert report.primary_design_type is ExperimentDesignType.LONGITUDINAL
    assert report.detected_design_types == (
        ExperimentDesignType.MULTI_GROUP,
        ExperimentDesignType.LONGITUDINAL,
        ExperimentDesignType.TMT_PLEXED,
    )
    assert (
        report.recommended_analysis_family
        is ExperimentDesignAnalysisFamily.TIME_COURSE_DIFFERENTIAL
    )


def test_design_classification_detects_batch_confounded_targeted_and_exploratory_types() -> (
    None
):
    confounded_design = build_experiment_design(
        (
            _entry(
                sample_id="C1",
                condition="control",
                spectra_file="run-c1",
                batch="batch-a",
            ),
            _entry(
                sample_id="T1",
                condition="treatment",
                spectra_file="run-t1",
                batch="batch-b",
            ),
        )
    )
    targeted_design = build_experiment_design(
        (
            _entry(
                sample_id="control_r1",
                condition="control",
                spectra_file="control_r1.raw",
                metadata={"analysis_intent": "targeted_validation"},
            ),
            _entry(
                sample_id="treat_r1",
                condition="treatment",
                spectra_file="treat_r1.raw",
                metadata={"analysis_intent": "targeted_validation"},
            ),
        )
    )
    exploratory_design = build_experiment_design(
        (
            _entry(
                sample_id="S1",
                condition="screen",
                spectra_file="run-001",
            ),
            _entry(
                sample_id="S2",
                condition="screen",
                spectra_file="run-002",
            ),
        )
    )

    confounded_report = build_experiment_design_classification_report(
        confounded_design,
        condition_a="control",
        condition_b="treatment",
        batch_field="batch",
    )
    targeted_report = build_experiment_design_classification_report(targeted_design)
    exploratory_report = build_experiment_design_classification_report(
        exploratory_design
    )

    assert (
        confounded_report.primary_design_type is ExperimentDesignType.BATCH_CONFOUNDED
    )
    assert (
        confounded_report.recommended_analysis_family
        is ExperimentDesignAnalysisFamily.EXPLORATORY_SUMMARY
    )
    assert (
        targeted_report.primary_design_type is ExperimentDesignType.TARGETED_VALIDATION
    )
    assert (
        targeted_report.recommended_analysis_family
        is ExperimentDesignAnalysisFamily.TARGETED_VALIDATION_REVIEW
    )
    assert exploratory_report.primary_design_type is ExperimentDesignType.EXPLORATORY
    assert (
        exploratory_report.recommended_analysis_family
        is ExperimentDesignAnalysisFamily.EXPLORATORY_SUMMARY
    )
    assert "primary_design_type" in render_experiment_design_classification_tsv(
        exploratory_report
    )


def test_require_matching_design_family_blocks_mismatched_methods() -> None:
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
        )
    )

    try:
        require_matching_experiment_design_analysis_family(
            design,
            chosen_analysis_family=ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL,
        )
    except ValueError as exc:
        assert "paired" in str(exc)
        assert "paired_differential" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected mismatched design family to be rejected")
