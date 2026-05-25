# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib


def test_runtime_handoff_import_contract() -> None:
    module = importlib.import_module("bijux_proteomics_runtime.handoff")

    assert module.build_handoff_archive is not None
    assert module.load_handoff_archive is not None
