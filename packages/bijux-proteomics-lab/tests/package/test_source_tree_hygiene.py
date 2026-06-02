# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

LAB_TEST_ROOT = Path("packages/bijux-proteomics-lab/tests")
LAB_TEST_FAMILIES = {
    "benchmarks",
    "design",
    "governance",
    "handoffs",
    "lifecycle",
    "outcomes",
    "package",
    "planning",
    "readiness",
    "reconciliation",
}
def test_lab_tests_tree_uses_operational_family_boundaries() -> None:
    family_directories = {
        path.name
        for path in LAB_TEST_ROOT.iterdir()
        if path.is_dir() and path.name != "fixtures"
    }
    flat_test_modules = sorted(
        path.relative_to(LAB_TEST_ROOT).as_posix()
        for path in LAB_TEST_ROOT.glob("test_*.py")
    )

    assert family_directories == LAB_TEST_FAMILIES
    assert flat_test_modules == []
