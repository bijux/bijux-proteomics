# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Compatibility facade for output protocol helper ownership."""

from __future__ import annotations

from .artifact_output import _emit_json, _read_identifier_lines, _write_text_output
from .protocol_policy import (
    _build_protocol_aware_selection_policy,
    _build_protocol_consistency_report_from_inputs,
    _load_protocol_context,
)
from .volcano_review import (
    _build_volcano_review_policy,
    _export_volcano_review_assets,
)
from .workflow_execution import (
    _run_orchestrated_workflow,
    _validate_proteomics_run_inputs,
)

__all__ = (
    "_build_protocol_aware_selection_policy",
    "_build_protocol_consistency_report_from_inputs",
    "_build_volcano_review_policy",
    "_emit_json",
    "_export_volcano_review_assets",
    "_load_protocol_context",
    "_read_identifier_lines",
    "_run_orchestrated_workflow",
    "_validate_proteomics_run_inputs",
    "_write_text_output",
)
