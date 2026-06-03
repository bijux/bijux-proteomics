# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.study import (
    ExperimentDesignAnalysisFamily,
    build_experiment_design,
    build_experiment_feasibility_report,
    render_experiment_feasibility_group_sizes_tsv,
    render_experiment_feasibility_invalid_contrasts_tsv,
    render_experiment_feasibility_missing_metadata_tsv,
    render_experiment_feasibility_model_support_tsv,
    render_experiment_feasibility_valid_contrasts_tsv,
    require_feasible_experiment_design_for_analysis,
)


def _entry(
    *,
    sample_id: str,
    condition: str,
    spectra_file: str,
    replicate: int = 1,
    batch: str | None = None,
    pair_id: str | None = None,
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
        metadata=metadata or {},
    )


def test_experiment_feasibility_report_lists_supported_and_unsupported_contrasts() -> (
    None
):
    design = build_experiment_design(
        (
            _entry(sample_id="C1", condition="control", spectra_file="c1.raw"),
            _entry(
                sample_id="C2",
                condition="control",
                spectra_file="c2.raw",
                replicate=2,
            ),
            _entry(sample_id="T1", condition="treatment", spectra_file="t1.raw"),
            _entry(
                sample_id="T2",
                condition="treatment",
                spectra_file="t2.raw",
                replicate=2,
            ),
            _entry(sample_id="R1", condition="recovery", spectra_file="r1.raw"),
        )
    )

    report = build_experiment_feasibility_report(design)

    assert report.summary.valid_contrast_count == 1
    assert report.summary.invalid_contrast_count == 2
    assert report.summary.underpowered_condition_count == 1
    assert report.valid_contrasts[0].condition_a == "control"
    assert report.valid_contrasts[0].condition_b == "treatment"
    assert report.valid_contrasts[0].supported is True
    assert all(
        "insufficient_group_size" in entry.reason_codes
        for entry in report.invalid_contrasts
    )
    assert report.group_sizes[-1].condition == "treatment"
    assert report.group_sizes[1].underpowered is True
    assert report.model_support[0].analysis_family is (
        ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL
    )
    assert report.model_support[0].supported is True
    assert any(
        entry.analysis_family
        is ExperimentDesignAnalysisFamily.MULTI_CONDITION_DIFFERENTIAL
        and not entry.supported
        for entry in report.model_support
    )
    assert "condition_a" in render_experiment_feasibility_valid_contrasts_tsv(report)
    assert (
        "insufficient_group_size"
        in render_experiment_feasibility_invalid_contrasts_tsv(report)
    )
    assert "effective_statistical_unit_count" in (
        render_experiment_feasibility_group_sizes_tsv(report)
    )
    assert "analysis_family" in render_experiment_feasibility_model_support_tsv(report)


def test_experiment_feasibility_report_detects_missing_metadata_and_rejected_rows(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tpair_id\tsample_role",
                "S1\tcontrol\t1\t1\trun-001.raw\tpair-1\tsample",
                "S2\ttreatment\t1\t1\trun-002.raw\t\tsample",
                "S3\ttreatment\t2\t1\trun-003.raw\tpair-2\tqc_bridge",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_experiment_feasibility_report(
        parse_experimental_design_table(design_path),
        pairing_field="pair_id",
        timepoint_field="timepoint",
    )

    assert report.parse_rejected_row_count == 1
    assert report.summary.missing_metadata_count == 3
    assert {issue.code for issue in report.missing_metadata} == {
        "rejected_design_rows",
        "missing_pairing_metadata",
        "missing_timepoint_metadata",
    }
    assert (
        "missing_timepoint_metadata"
        in render_experiment_feasibility_missing_metadata_tsv(report)
    )


def test_require_feasible_experiment_design_blocks_impossible_models() -> None:
    design = build_experiment_design(
        (
            _entry(
                sample_id="subject-1_t0",
                condition="control",
                spectra_file="subject-1_t0.raw",
                pair_id="subject-1",
                metadata={"timepoint": "T0"},
            ),
            _entry(
                sample_id="subject-1_t1",
                condition="control",
                spectra_file="subject-1_t1.raw",
                pair_id="subject-1",
                replicate=2,
                metadata={"timepoint": "T1"},
            ),
        )
    )

    try:
        require_feasible_experiment_design_for_analysis(
            design,
            chosen_analysis_family=ExperimentDesignAnalysisFamily.PAIRWISE_DIFFERENTIAL,
        )
    except ValueError as exc:
        assert "not feasible" in str(exc)
        assert "different_analysis_family_required" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected unsupported pairwise model to be rejected")
