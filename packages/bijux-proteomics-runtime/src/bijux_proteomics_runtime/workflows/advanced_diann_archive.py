# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Archive and rehydrate completed advanced DIA-NN runtime runs."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    ProteomicsStudyResultSummary,
    ResultManifestReport,
    build_result_manifest_from_artifacts,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.support.workspace import write_text_atomic
from bijux_proteomics_runtime.workflows.advanced_diann import (
    AdvancedDiannRuntimeRunReport,
    AdvancedDiannRuntimeStatus,
)

_ADVANCED_DIANN_ARCHIVE_COMMAND = (
    "bijux_proteomics_runtime.workflows.advanced_diann_archive."
    "archive_completed_advanced_diann_run"
)
_ADVANCED_DIANN_RUNTIME_COMMAND = (
    "bijux_proteomics_runtime.workflows.advanced_diann."
    "run_resumable_advanced_diann_workflow"
)


class AdvancedDiannCompletedRunArtifacts(JsonModel):
    """Stable archive artifacts written for one completed advanced DIA-NN run."""

    model_config = ConfigDict(extra="forbid")

    biological_report_dir: str = Field(..., min_length=1)
    result_manifest_json: str = Field(..., min_length=1)
    completed_run_report_json: str = Field(..., min_length=1)


class AdvancedDiannCompletedRunArchiveReport(JsonModel):
    """Archive validation report for one completed advanced DIA-NN runtime run."""

    model_config = ConfigDict(extra="forbid")

    config: AdvancedDiannWorkflowConfig
    runtime_report: AdvancedDiannRuntimeRunReport | None = None
    result_manifest: ResultManifestReport
    study_result_summary: ProteomicsStudyResultSummary
    archive_validated: bool
    artifacts: AdvancedDiannCompletedRunArtifacts
    note: str = Field(..., min_length=1)


def archive_completed_advanced_diann_run(
    config: AdvancedDiannWorkflowConfig,
    *,
    runtime_report: AdvancedDiannRuntimeRunReport | None = None,
) -> AdvancedDiannCompletedRunArchiveReport:
    """Persist a governed completed-run archive for one advanced DIA-NN runtime run."""

    if runtime_report is not None:
        if runtime_report.status is not AdvancedDiannRuntimeStatus.COMPLETED:
            raise ValueError(
                "advanced dia-nn archiving requires a completed runtime run report"
            )
        if runtime_report.advanced_report is None:
            raise ValueError(
                "advanced dia-nn archiving requires a completed advanced workflow report"
            )

    biological_report_dir = config.output_dir.resolve()
    commands = [_ADVANCED_DIANN_ARCHIVE_COMMAND]
    if runtime_report is not None:
        commands.insert(0, _ADVANCED_DIANN_RUNTIME_COMMAND)
    result_manifest = build_result_manifest_from_artifacts(
        biological_report_dir=biological_report_dir,
        commands=tuple(commands),
    )
    if result_manifest.summary.missing_required_file_count != 0:
        raise ValueError(
            "advanced dia-nn archiving requires a complete governed biological output "
            "directory"
        )

    result_manifest_path = config.output_dir / "result_manifest.json"
    write_text_atomic(result_manifest_path, result_manifest.to_stable_json() + "\n")
    study_result = load_completed_run(config.output_dir)
    artifacts = AdvancedDiannCompletedRunArtifacts(
        biological_report_dir=str(biological_report_dir),
        result_manifest_json=str(result_manifest_path.resolve()),
        completed_run_report_json=str(
            (config.output_dir / "advanced_diann_completed_run_report.json").resolve()
        ),
    )
    report = AdvancedDiannCompletedRunArchiveReport(
        config=config,
        runtime_report=runtime_report,
        result_manifest=result_manifest,
        study_result_summary=study_result.summary,
        archive_validated=True,
        artifacts=artifacts,
        note=(
            "advanced dia-nn completed-run archiving builds a governed result manifest "
            "from the completed workflow output directory and proves the archive can be "
            "rehydrated through the runtime result loader"
        ),
    )
    write_text_atomic(
        config.output_dir / "advanced_diann_completed_run_report.json",
        report.to_stable_json() + "\n",
    )
    return report


__all__ = [
    "AdvancedDiannCompletedRunArchiveReport",
    "AdvancedDiannCompletedRunArtifacts",
    "archive_completed_advanced_diann_run",
]
