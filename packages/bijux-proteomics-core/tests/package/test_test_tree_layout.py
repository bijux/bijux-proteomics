# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

TEST_ROOT = Path("packages/bijux-proteomics-core/tests")
PACKAGE_TEST_ROOT = TEST_ROOT / "package"


def test_root_level_core_tests_stay_empty_after_package_family_split() -> None:
    root_level_tests = {
        path.name for path in TEST_ROOT.glob("test_*.py") if path.is_file()
    }
    package_tests = {
        path.name for path in PACKAGE_TEST_ROOT.glob("test_*.py") if path.is_file()
    }

    assert root_level_tests == set()
    assert package_tests == {
        "test_compatibility_exports.py",
        "test_core_boundary_guards.py",
        "test_cross_package_invariants.py",
        "test_foundation_hashing_surface.py",
        "test_foundation_primitives_surface.py",
        "test_owner_wrapper_guards.py",
        "test_package_charter.py",
        "test_public_api_surface.py",
        "test_source_tree_hygiene.py",
        "test_test_tree_layout.py",
    }
