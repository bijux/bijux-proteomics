# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_streaming_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.streaming")

    assert module.StreamingImportStep is not None
    assert module.StreamingImportReport is not None
    assert module.iter_streaming_import_batches is not None
    assert module.run_streaming_import_step is not None
