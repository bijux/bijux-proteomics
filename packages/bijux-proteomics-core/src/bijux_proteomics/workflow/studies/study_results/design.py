# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Design normalization helpers for study-result builders."""

from __future__ import annotations

from collections.abc import Iterable

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyDesignEntry,
    ProteomicsStudyDesignSnapshot,
)


def _design_from_biological_report(
    report: BiologicalResultReportBundle,
) -> ProteomicsStudyDesignSnapshot:
    return _design_from_sample_metadata(
        (
            ProteomicsStudyDesignEntry(
                sample_id=entry.sample_id,
                condition=entry.condition,
                batch=entry.batch,
            )
            for entry in report.sample_exploration_report.sample_pca_report.entries
        ),
        note=(
            "design snapshot reconstructed from biological sample exploration so "
            "downstream study results remain comparable even when the source bundle "
            "stores only the governed biology surface"
        ),
    )


def _design_from_tmt_workflow(
    bundle: TmtExperimentWorkflowBundle,
) -> ProteomicsStudyDesignSnapshot:
    return _design_from_sample_metadata(
        (
            ProteomicsStudyDesignEntry(
                sample_id=entry.sample_id,
                condition=entry.condition,
                multiplex_group=entry.multiplex_group,
                sample_role=entry.sample_role,
            )
            for entry in bundle.report.sample_qc_entries
        ),
        note=(
            "design snapshot preserved from tmt sample qc and multiplex metadata "
            "surfaces for programmatic cross-study comparison"
        ),
    )


def _design_from_experimental_entries(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> ProteomicsStudyDesignSnapshot:
    return _design_from_sample_metadata(
        (
            ProteomicsStudyDesignEntry(
                sample_id=entry.sample_id,
                condition=entry.condition,
                replicate=str(entry.replicate),
                fraction=str(entry.fraction),
                batch=entry.batch,
                pair_id=entry.pair_id,
                multiplex_group=entry.multiplex_group,
                multiplex_channel=entry.multiplex_channel,
                sample_role=entry.sample_role.value,
            )
            for entry in entries
        ),
        note="design snapshot preserved directly from owned experimental design entries",
    )


def _design_from_sample_metadata(
    entries: Iterable[ProteomicsStudyDesignEntry],
    *,
    note: str,
) -> ProteomicsStudyDesignSnapshot:
    stable_entries: tuple[ProteomicsStudyDesignEntry, ...] = tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.sample_id,
                entry.condition or "",
                entry.replicate or "",
                entry.fraction or "",
            ),
        )
    )
    return ProteomicsStudyDesignSnapshot(
        entries=stable_entries,
        sample_count=len(stable_entries),
        condition_count=len(
            {entry.condition for entry in stable_entries if entry.condition}
        ),
        batch_count=len({entry.batch for entry in stable_entries if entry.batch}),
        paired_sample_count=sum(1 for entry in stable_entries if entry.pair_id),
        multiplexed_sample_count=sum(
            1
            for entry in stable_entries
            if entry.multiplex_group or entry.multiplex_channel
        ),
        note=note,
    )


__all__ = [
    "_design_from_biological_report",
    "_design_from_experimental_entries",
    "_design_from_sample_metadata",
    "_design_from_tmt_workflow",
]
