# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_foundation.testing.source_tree_complexity import (
    SourceFunctionComplexityException,
    build_source_tree_complexity_report,
)


def test_source_tree_complexity_report_classifies_approved_and_unexpected_functions(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "module.py").write_text(
        "def small():\n"
        "    return 1\n\n"
        "def approved(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    if not x:\n"
        "        return 2\n"
        "    return 3\n\n"
        "def unexpected(x, y, z):\n"
        "    if x:\n"
        "        return 1\n"
        "    if y:\n"
        "        return 2\n"
        "    if z:\n"
        "        return 3\n"
        "    return 4\n"
    )

    report = build_source_tree_complexity_report(
        source_root,
        ceiling=2,
        exceptions=(
            SourceFunctionComplexityException(
                relative_path="module.py",
                qualified_name="approved",
                allowed_complexity=3,
                temporary_reason="temporary complex owner allowance",
            ),
        ),
    )

    assert report.scanned_function_count == 3
    assert report.skipped_marked_generated_count == 0
    assert tuple(
        (item.relative_path, item.qualified_name, item.complexity)
        for item in report.approved_over_ceiling
    ) == (("module.py", "approved", 3),)
    assert tuple(
        (item.relative_path, item.qualified_name, item.complexity)
        for item in report.unexpected_over_ceiling
    ) == (("module.py", "unexpected", 4),)
    assert report.stale_exceptions == ()


def test_source_tree_complexity_report_flags_stale_and_exceeded_exceptions(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "module.py").write_text(
        "class Example:\n"
        "    def still_too_complex(self, x, y, z):\n"
        "        if x:\n"
        "            return 1\n"
        "        if y:\n"
        "            return 2\n"
        "        if z:\n"
        "            return 3\n"
        "        return 4\n\n"
        "    def no_longer_complex(self):\n"
        "        return 1\n"
    )

    report = build_source_tree_complexity_report(
        source_root,
        ceiling=2,
        exceptions=(
            SourceFunctionComplexityException(
                relative_path="module.py",
                qualified_name="Example.still_too_complex",
                allowed_complexity=3,
                temporary_reason="temporary complex owner allowance",
            ),
            SourceFunctionComplexityException(
                relative_path="module.py",
                qualified_name="Example.no_longer_complex",
                allowed_complexity=3,
                temporary_reason="stale exception should be removed",
            ),
        ),
    )

    assert tuple(
        (item.relative_path, item.qualified_name, item.complexity)
        for item in report.unexpected_over_ceiling
    ) == (("module.py", "Example.still_too_complex", 4),)
    assert tuple(
        (item.relative_path, item.qualified_name) for item in report.stale_exceptions
    ) == (("module.py", "Example.no_longer_complex"),)


def test_source_tree_complexity_report_can_skip_marked_generated_files(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "generated_complex.py").write_text(
        "# Generated generated-complexity fixture.\n"
        "# Regenerate with: ./.venv/bin/python -m repo.generated.complexity\n\n"
        "def generated(x, y, z):\n"
        "    if x:\n"
        "        return 1\n"
        "    if y:\n"
        "        return 2\n"
        "    if z:\n"
        "        return 3\n"
        "    return 4\n",
        encoding="utf-8",
    )

    report = build_source_tree_complexity_report(
        source_root,
        ceiling=2,
        exclude_marked_generated=True,
    )

    assert report.scanned_function_count == 0
    assert report.skipped_marked_generated_count == 1
    assert report.approved_over_ceiling == ()
    assert report.unexpected_over_ceiling == ()
