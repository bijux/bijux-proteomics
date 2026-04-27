# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib

from agentic_proteins.core.stability import STABILITY_EXPECTATIONS


def test_module_stability_annotations() -> None:
    assert "bijux_proteomics_runtime.providers" in STABILITY_EXPECTATIONS
    assert "bijux_proteomics_runtime.runtime" in STABILITY_EXPECTATIONS
    for module_path, expected in STABILITY_EXPECTATIONS.items():
        module = importlib.import_module(module_path)
        actual = getattr(module, "__stability__", None)
        assert actual == expected, (
            f"Stability annotation missing or mismatched for {module_path}."
        )
