# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run configuration model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RunConfig(BaseModel):
    """RunConfig."""

    model_config = ConfigDict(extra="forbid")

    predictors_enabled: list[str] | None = Field(
        default=None,
        description="Enabled provider names; defaults to heuristic_proxy.",
    )
    resource_limits: dict[str, float] | None = Field(
        default=None,
        description="Resource limits (cpu_seconds, gpu_seconds).",
    )
    retry_policy: dict[str, int] | None = Field(
        default=None,
        description="Retry policy (max_retries).",
    )
    logging_enabled: bool | None = Field(
        default=None,
        description="Enable structured logging.",
    )
    dry_run: bool | None = Field(
        default=None,
        description="Plan and validate without executing tools.",
    )
    strict_mode: bool | None = Field(
        default=None,
        description="Treat warnings as errors; forbid fallbacks.",
    )
    loop_max_iterations: int | None = Field(
        default=None,
        description="Max iterations in the agentic loop.",
    )
    loop_stagnation_window: int | None = Field(
        default=None,
        description="Iterations to consider for stagnation detection.",
    )
    loop_improvement_threshold: float | None = Field(
        default=None,
        description="Minimum improvement delta to avoid stagnation.",
    )
    loop_max_cost: float | None = Field(
        default=None,
        description="Maximum total cost for a loop.",
    )
    seed: int | None = Field(
        default=None,
        description="Deterministic seed for tool runs.",
    )
    tool_versions: dict[str, str] | None = Field(
        default=None,
        description="Tool versions used for deterministic replay.",
    )
    require_human_decision: bool | None = Field(
        default=None,
        description="Require signed human decision before completing a run.",
    )
    artifacts_dir: str | None = Field(
        default=None,
        description="Override artifacts root directory for this run.",
    )
    execution_mode: str | None = Field(
        default=None,
        description="Execution mode for providers: auto, gpu, or cpu.",
    )

    def with_defaults(self) -> tuple[RunConfig, list[str]]:
        """with_defaults."""
        warnings: list[str] = []
        data = self.model_dump()
        if data["predictors_enabled"] is None:
            data["predictors_enabled"] = ["heuristic_proxy"]
            warnings.append("default_predictors_enabled")
        if data["resource_limits"] is None:
            data["resource_limits"] = {"cpu_seconds": 0.0, "gpu_seconds": 0.0}
            warnings.append("default_resource_limits")
        if data["retry_policy"] is None:
            data["retry_policy"] = {"max_retries": 0}
            warnings.append("default_retry_policy")
        if data["logging_enabled"] is None:
            data["logging_enabled"] = True
            warnings.append("default_logging_enabled")
        if data["dry_run"] is None:
            data["dry_run"] = False
            warnings.append("default_dry_run")
        if data["strict_mode"] is None:
            data["strict_mode"] = False
            warnings.append("default_strict_mode")
        if data["loop_max_iterations"] is None:
            data["loop_max_iterations"] = 1
            warnings.append("default_loop_max_iterations")
        if data["loop_stagnation_window"] is None:
            data["loop_stagnation_window"] = 2
            warnings.append("default_loop_stagnation_window")
        if data["loop_improvement_threshold"] is None:
            data["loop_improvement_threshold"] = 0.5
            warnings.append("default_loop_improvement_threshold")
        if data["loop_max_cost"] is None:
            data["loop_max_cost"] = 1.0
            warnings.append("default_loop_max_cost")
        if data["seed"] is None:
            data["seed"] = 0
            warnings.append("default_seed")
        if data["tool_versions"] is None:
            data["tool_versions"] = {}
            warnings.append("default_tool_versions")
        if data["require_human_decision"] is None:
            data["require_human_decision"] = False
            warnings.append("default_require_human_decision")
        if data["artifacts_dir"] is None:
            data["artifacts_dir"] = None
        if data["execution_mode"] is None:
            data["execution_mode"] = "auto"
        return RunConfig(**data), warnings
