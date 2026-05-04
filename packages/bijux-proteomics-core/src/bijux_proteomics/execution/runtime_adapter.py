# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Adapters from core execution requests into concrete runtimes."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.execution.backend import ExecutionBackend, ExecutionRequest


class AgenticProteinsBackend:
    """Execution backend backed by the Agentic Proteins runtime."""

    def execute(self, request: ExecutionRequest) -> dict[str, Any]:
        """Execute a core request through the runtime RunManager entrypoint."""
        from agentic_proteins.runtime import RunManager
        from agentic_proteins.runtime.infra import RunConfig

        config = RunConfig(
            loop_max_iterations=request.rounds,
            predictors_enabled=[request.provider] if request.provider else None,
            artifacts_dir=str(request.artifacts_dir) if request.artifacts_dir else None,
            execution_mode=request.execution_mode,
            require_human_decision=request.require_human_decision,
        )
        return RunManager(base_dir=request.base_dir, config=config).run(
            request.candidate_sequence
        )


class MissingExecutionBackendError(RuntimeError):
    """Raised when no execution backend is supplied to core."""


def require_backend(backend: ExecutionBackend | None) -> ExecutionBackend:
    """Return a configured backend or raise a clear error."""
    if backend is None:
        raise MissingExecutionBackendError(
            "program execution requires an injected ExecutionBackend"
        )
    return backend
