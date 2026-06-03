# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_scientific_checkpoint_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.checkpoints")

    assert module.ScientificCheckpointInput is not None
    assert module.ScientificCheckpointReport is not None
    assert module.build_scientific_checkpoints is not None
