# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

WRAPPER_MODULES = (
    "packages/bijux-proteomics-core/src/bijux_proteomics/execution/providers.py",
    "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/api.py",
    "packages/bijux-proteomics-core/src/bijux_proteomics/intelligence/__init__.py",
    "packages/bijux-proteomics-core/src/bijux_proteomics/workflow/reproducibility.py",
    "packages/bijux-proteomics-core/src/bijux_proteomics/workflow/runs.py",
    "packages/bijux-proteomics-core/src/bijux_proteomics/workflow/runtime.py",
)


def test_owner_wrapper_modules_remain_thin_forwarders() -> None:
    for relative_path in WRAPPER_MODULES:
        content = (REPO_ROOT / relative_path).read_text()
        assert "import *" in content, f"{relative_path} must forward to a canonical owner"
        assert "\nclass " not in content, f"{relative_path} must not carry local models"
        assert "\ndef " not in content, f"{relative_path} must not carry local behavior"
