# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.execution.analysis import RunAnalysis
from agentic_proteins.execution.artifacts import load_artifact
from agentic_proteins.execution.logging import StructuredLogger
from agentic_proteins.execution.manager import RunManager
from agentic_proteins.execution.run_config import RunConfig
from agentic_proteins.execution.state_machine import RunStateMachine
from agentic_proteins.execution.telemetry import TelemetryClient
from agentic_proteins.execution.tool_reliability import ToolReliabilityTracker
from bijux_proteomics_runtime.runs.analysis import RunAnalysis as RuntimeRunAnalysis
from bijux_proteomics_runtime.runs.artifacts import load_artifact as runtime_load_artifact
from bijux_proteomics_runtime.runs.logging import StructuredLogger as RuntimeStructuredLogger
from bijux_proteomics_runtime.runs.manager import RunManager as RuntimeRunManager
from bijux_proteomics_runtime.runs.run_config import RunConfig as RuntimeRunConfig
from bijux_proteomics_runtime.runs.state_machine import (
    RunStateMachine as RuntimeRunStateMachine,
)
from bijux_proteomics_runtime.runs.telemetry import TelemetryClient as RuntimeTelemetryClient
from bijux_proteomics_runtime.runs.tool_reliability import (
    ToolReliabilityTracker as RuntimeToolReliabilityTracker,
)


def test_run_execution_surface_forwards_to_runtime_symbols() -> None:
    assert RunManager is RuntimeRunManager
    assert RunConfig is RuntimeRunConfig
    assert RunAnalysis is RuntimeRunAnalysis
    assert StructuredLogger is RuntimeStructuredLogger
    assert TelemetryClient is RuntimeTelemetryClient
    assert ToolReliabilityTracker is RuntimeToolReliabilityTracker
    assert RunStateMachine is RuntimeRunStateMachine
    assert load_artifact is runtime_load_artifact
