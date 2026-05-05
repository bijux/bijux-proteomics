# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runtime.control.workflow_reproducibility import (
    CacheDecisionOutcome,
    WorkflowCacheProbe,
    WorkflowCacheRecord,
    explain_workflow_cache_decisions,
)


def test_explain_workflow_cache_decisions_reports_hit_miss_and_refused() -> None:
    report = explain_workflow_cache_decisions(
        probes=(
            WorkflowCacheProbe(
                step_id="quant",
                tool_name="lfq",
                schema_ref="schema.quant.v1",
                parameter_fingerprint="a" * 16,
                input_fingerprint="b" * 16,
                environment_fingerprint="c" * 16,
                policy_fingerprint="d" * 16,
            ),
            WorkflowCacheProbe(
                step_id="qc",
                tool_name="qc",
                schema_ref="schema.qc.v1",
                parameter_fingerprint="e" * 16,
                input_fingerprint="f" * 16,
                environment_fingerprint="g" * 16,
                policy_fingerprint="h" * 16,
                cache_allowed=False,
            ),
        ),
        cache_records=(
            WorkflowCacheRecord(
                record_id="cache-1",
                tool_name="lfq",
                schema_ref="schema.quant.v1",
                parameter_fingerprint="a" * 16,
                input_fingerprint="b" * 16,
                environment_fingerprint="c" * 16,
                policy_fingerprint="d" * 16,
            ),
        ),
    )

    assert report.hit_count == 1
    assert report.refused_count == 1
    assert report.miss_count == 0
    assert report.entries[0].outcome is CacheDecisionOutcome.HIT
