# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .workflow_golden_support import WORKFLOW_GOLDEN_TARGETS, WORKFLOW_GOLDEN_ROOT


def test_key_workflow_golden_directories_cover_all_required_workflows() -> None:
    assert set(WORKFLOW_GOLDEN_TARGETS) == {
        "advanced_diann",
        "advanced_maxquant",
        "advanced_fragpipe",
        "advanced_ptm",
        "advanced_tmt",
        "advanced_targeted",
    }

    fixture_directories = {
        path.name for path in WORKFLOW_GOLDEN_ROOT.iterdir() if path.is_dir()
    }
    assert fixture_directories == set(WORKFLOW_GOLDEN_TARGETS)


def test_key_workflow_golden_directories_keep_manifest_and_three_review_files() -> None:
    for workflow_name, file_names in WORKFLOW_GOLDEN_TARGETS.items():
        fixture_dir = WORKFLOW_GOLDEN_ROOT / workflow_name
        assert file_names[0] == "manifest.json"
        assert len(file_names) == 4
        assert {path.name for path in fixture_dir.iterdir() if path.is_file()} == set(
            file_names
        )
