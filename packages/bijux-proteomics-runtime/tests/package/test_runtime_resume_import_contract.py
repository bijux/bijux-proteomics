# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_resume_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.resume")

    assert module.WorkflowResumeConfig is not None
    assert module.WorkflowResumeState is not None
    assert module.resume_workflow is not None
