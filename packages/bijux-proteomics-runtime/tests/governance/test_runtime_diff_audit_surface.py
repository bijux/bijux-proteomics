# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_CHARTER_ENTRIES,
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeCharterCapability,
    RuntimeModuleClassification,
)


def test_runtime_diff_owner_is_required_for_reviewable_completed_run_diffs() -> None:
    review_entry = next(
        entry
        for entry in DEFAULT_RUNTIME_CHARTER_ENTRIES
        if entry.capability is RuntimeCharterCapability.REVIEWABLE_OUTPUTS
    )

    assert "diff/completed_runs.py" in review_entry.required_modules


def test_runtime_diff_owner_is_audited_as_execution_value() -> None:
    audit_entry = next(
        entry
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.module_path == "diff/completed_runs.py"
    )

    assert audit_entry.classification is RuntimeModuleClassification.EXECUTION_VALUE
    assert audit_entry.anchor_capabilities == (
        RuntimeCharterCapability.REVIEWABLE_OUTPUTS,
    )
