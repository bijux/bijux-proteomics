# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_reproducibility import (
    StableRuntimeErrorClass,
    build_stable_runtime_error_envelope,
)


def test_build_stable_runtime_error_envelope_normalizes_code_and_context() -> None:
    envelope = build_stable_runtime_error_envelope(
        error_class=StableRuntimeErrorClass.RUNTIME,
        code="Engine Timeout",
        message="external engine did not complete before timeout",
        evidence_pointer="run-77:step-search:log",
        remediation="increase timeout or reduce input shard size",
        transient=True,
        context={"step_id": "search", "run_id": "run-77"},
    )

    assert envelope.error_class is StableRuntimeErrorClass.RUNTIME
    assert envelope.code == "engine_timeout"
    assert envelope.context[0] == ("run_id", "run-77")
