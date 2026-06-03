# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.study import (
    detect_batch_condition_confounding,
    render_batch_condition_confounding_tsv,
)


def test_batch_condition_confounding_blocks_fully_aliased_case_control_contrast() -> (
    None
):
    report = detect_batch_condition_confounding(
        (
            ExperimentalDesignEntry(
                sample_id="case-1",
                condition="case",
                replicate=1,
                fraction=1,
                spectra_file="case-1.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="case-2",
                condition="case",
                replicate=2,
                fraction=1,
                spectra_file="case-2.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="ctrl-1.mzml",
                batch="batch-b",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="ctrl-2.mzml",
                batch="batch-b",
            ),
        )
    )
    rendered = render_batch_condition_confounding_tsv(report)

    assert report.is_confounded is True
    assert report.confounded_terms == ("case:batch-a", "control:batch-b")
    assert report.blocked_contrasts == ("case_vs_control",)
    assert "fully aliased with condition labels" in report.reason
    assert "blocked_contrasts" in rendered


def test_batch_condition_confounding_leaves_balanced_batches_unblocked() -> None:
    report = detect_batch_condition_confounding(
        (
            ExperimentalDesignEntry(
                sample_id="case-a",
                condition="case",
                replicate=1,
                fraction=1,
                spectra_file="case-a.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-a",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="ctrl-a.mzml",
                batch="batch-a",
            ),
            ExperimentalDesignEntry(
                sample_id="case-b",
                condition="case",
                replicate=2,
                fraction=1,
                spectra_file="case-b.mzml",
                batch="batch-b",
            ),
            ExperimentalDesignEntry(
                sample_id="ctrl-b",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="ctrl-b.mzml",
                batch="batch-b",
            ),
        )
    )

    assert report.is_confounded is False
    assert report.confounded_terms == ()
    assert report.blocked_contrasts == ()
    assert "do not fully block" in report.reason
