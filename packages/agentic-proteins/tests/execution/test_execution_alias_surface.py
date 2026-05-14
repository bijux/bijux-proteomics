from __future__ import annotations

from agentic_proteins.execution import RunAnalysis, RunConfig, ToolReliabilityTracker
from agentic_proteins.execution.runtime import executor as legacy_executor
from bijux_proteomics_runtime.execution.engine.executor import LocalExecutor
from bijux_proteomics_runtime.runs.analysis import RunAnalysis as RuntimeRunAnalysis
from bijux_proteomics_runtime.runs.run_config import RunConfig as RuntimeRunConfig
from bijux_proteomics_runtime.runs.tool_reliability import (
    ToolReliabilityTracker as RuntimeToolReliabilityTracker,
)


def test_execution_aliases_keep_runtime_owner_types_intact() -> None:
    assert RunConfig is RuntimeRunConfig
    assert RunAnalysis is RuntimeRunAnalysis
    assert ToolReliabilityTracker is RuntimeToolReliabilityTracker


def test_execution_runtime_executor_alias_keeps_runtime_owner_exports() -> None:
    assert legacy_executor.LocalExecutor is LocalExecutor
