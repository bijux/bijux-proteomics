# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Frozen contracts for reviewable runtime execution."""

from __future__ import annotations

EXECUTION_REVIEW_CONTRACT = {
    "sequence_review_path": "bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
    "import_review_path": "bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
    "rerun_planning": "bijux_proteomics_runtime.runtime.control.build_runtime_partial_rerun_plan",
    "local_bundle_loader": "bijux_proteomics_runtime.runtime.control.load_local_run_bundle",
    "failure_report_writer": "bijux_proteomics_runtime.runtime.control.write_runtime_failure_report",
}

__all__ = ["EXECUTION_REVIEW_CONTRACT"]
