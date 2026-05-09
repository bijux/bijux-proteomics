# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

WRAPPER_MODULES: tuple[str, ...] = ()


def test_root_level_owner_wrapper_modules_are_removed() -> None:
    removed = (
        "packages/bijux-proteomics-core/src/bijux_proteomics/liabilities.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/search_adapters.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/workflow_blueprint.py",
    )

    for relative_path in removed:
        assert not (REPO_ROOT / relative_path).exists()


def test_remaining_non_root_wrapper_modules_remain_thin_forwarders() -> None:
    for relative_path in WRAPPER_MODULES:
        content = (REPO_ROOT / relative_path).read_text()
        assert "import *" in content, (
            f"{relative_path} must forward to a canonical owner"
        )
        assert "\nclass " not in content, f"{relative_path} must not carry local models"
        assert "\ndef " not in content, f"{relative_path} must not carry local behavior"


def test_removed_non_root_wrapper_modules_do_not_return() -> None:
    removed = (
        "packages/bijux-proteomics-core/src/bijux_proteomics/intelligence/__init__.py",
    )

    for relative_path in removed:
        assert not (REPO_ROOT / relative_path).exists()
