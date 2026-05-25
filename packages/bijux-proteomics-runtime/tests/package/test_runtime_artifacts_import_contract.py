# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_artifacts_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.artifacts")

    assert module.StepArtifact is not None
    assert module.build_step_artifact is not None
