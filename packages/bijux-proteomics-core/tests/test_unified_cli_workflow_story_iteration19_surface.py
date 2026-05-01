# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.product_api_iteration19 import (
    CliWorkflowCommandEntry,
    build_unified_cli_workflow_story,
)


def test_build_unified_cli_workflow_story_identifies_internal_commands() -> None:
    report = build_unified_cli_workflow_story(
        (
            CliWorkflowCommandEntry(
                command="bijux workflow-dda-import",
                workflow_id="workflow.dda-import",
                scientific_question="Which proteins are confidently identified in this run?",
            ),
            CliWorkflowCommandEntry(
                command="bijux internal-module-parse",
                workflow_id="workflow.internal-parse",
                scientific_question="Should not be exposed as user-facing workflow.",
            ),
        )
    )

    assert report.coherent_story is False
    assert report.internal_surface_commands == ("bijux internal-module-parse",)
