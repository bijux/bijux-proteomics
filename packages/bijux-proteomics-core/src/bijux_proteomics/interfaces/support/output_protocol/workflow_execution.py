# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Workflow execution and flagship-run input validation helpers."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.review.explanations.failure_explanations import (
    FailureExplanationRequest,
    build_failure_explanation_report,
    format_failure_explanation_for_cli,
)
from bijux_proteomics.workflow.pipelines.flagship_run import ProteomicsRunEngine
from bijux_proteomics.workflow.pipelines.orchestrator import (
    WorkflowConfig,
    WorkflowResult,
    run_proteomics_workflow,
)


def _run_orchestrated_workflow(config: WorkflowConfig) -> WorkflowResult:
    try:
        return run_proteomics_workflow(config)
    except Exception as exc:  # noqa: BLE001
        workflow_name = getattr(getattr(config, "mode", None), "value", None)
        report = build_failure_explanation_report(
            (
                FailureExplanationRequest(
                    failure_id="workflow_failure",
                    workflow_name=workflow_name,
                    failure_text=str(exc),
                ),
            )
        )
        raise click.ClickException(
            format_failure_explanation_for_cli(report.explanations[0])
        ) from exc


def _validate_proteomics_run_inputs(
    *,
    engine: ProteomicsRunEngine,
    report_path: Path | None,
    peptides_path: Path | None,
    protein_groups_path: Path | None,
    source_protein_tsv: Path | None,
    config_path: Path | None,
) -> None:
    if report_path is None:
        raise click.ClickException("--report is required")
    if engine is ProteomicsRunEngine.MAXQUANT:
        if peptides_path is None:
            raise click.ClickException(
                "MaxQuant runs require --peptides with peptides.txt"
            )
        if protein_groups_path is None:
            raise click.ClickException(
                "MaxQuant runs require --protein-groups with proteinGroups.txt"
            )
        return
    if peptides_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --peptides; that input is MaxQuant-specific"
        )
    if protein_groups_path is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --protein-groups; that input is MaxQuant-specific"
        )
    if engine is not ProteomicsRunEngine.FRAGPIPE and source_protein_tsv is not None:
        raise click.ClickException(
            f"{engine.value} runs do not accept --source-protein-tsv; that input is FragPipe-specific"
        )
    if engine is ProteomicsRunEngine.FRAGPIPE and config_path is not None:
        raise click.ClickException(
            "fragpipe runs do not accept --config-path in the flagship command"
        )
