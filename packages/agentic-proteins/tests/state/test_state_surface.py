# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.state.context import RunContext, create_run_context
from agentic_proteins.state.lifecycle import RunLifecycleState
from agentic_proteins.state.output import RunOutput, RunStatus, VersionInfo
from agentic_proteins.state.request import RunRequest
from agentic_proteins.state.schemas import StateSnapshot
from agentic_proteins.state.snapshot import snapshot_replan, snapshot_state
from agentic_proteins.state.workspace import RunWorkspace
from bijux_proteomics_runtime.runs.context import (
    RunContext as RuntimeRunContext,
)
from bijux_proteomics_runtime.runs.context import (
    create_run_context as runtime_create_run_context,
)
from bijux_proteomics_runtime.runs.lifecycle import (
    RunLifecycleState as RuntimeRunLifecycleState,
)
from bijux_proteomics_runtime.runs.output import (
    RunOutput as RuntimeRunOutput,
)
from bijux_proteomics_runtime.runs.output import (
    RunStatus as RuntimeRunStatus,
)
from bijux_proteomics_runtime.runs.output import (
    VersionInfo as RuntimeVersionInfo,
)
from bijux_proteomics_runtime.runs.request import RunRequest as RuntimeRunRequest
from bijux_proteomics_runtime.state.schemas import StateSnapshot as RuntimeStateSnapshot
from bijux_proteomics_runtime.state.snapshot import (
    snapshot_replan as runtime_snapshot_replan,
)
from bijux_proteomics_runtime.state.snapshot import (
    snapshot_state as runtime_snapshot_state,
)
from bijux_proteomics_runtime.support.workspace import (
    RunWorkspace as RuntimeRunWorkspace,
)


def test_state_surface_forwards_to_runtime_symbols() -> None:
    assert RunContext is RuntimeRunContext
    assert create_run_context is runtime_create_run_context
    assert RunLifecycleState is RuntimeRunLifecycleState
    assert RunOutput is RuntimeRunOutput
    assert RunStatus is RuntimeRunStatus
    assert VersionInfo is RuntimeVersionInfo
    assert RunRequest is RuntimeRunRequest
    assert StateSnapshot is RuntimeStateSnapshot
    assert snapshot_state is runtime_snapshot_state
    assert snapshot_replan is runtime_snapshot_replan
    assert RunWorkspace is RuntimeRunWorkspace
