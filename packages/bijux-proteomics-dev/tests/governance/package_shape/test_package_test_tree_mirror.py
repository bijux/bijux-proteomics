from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_test_tree_mirror import (
    PACKAGE_TEST_TREE_MIRROR_PATH,
    build_package_test_tree_mirror_report,
    run,
    validate_package_test_tree_mirror,
)


def test_package_test_tree_mirror_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_test_tree_mirror_report_tracks_source_alignment() -> None:
    report = build_package_test_tree_mirror_report()
    entries = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_TEST_TREE_MIRROR_PATH.exists()
    assert len(report.entries) == 8
    assert entries["bijux-proteomics-knowledge"].missing_test_families == ()
    assert entries["bijux-proteomics-lab"].missing_test_families == ("governance",)
    assert "benchmarks" in entries["bijux-proteomics-core"].missing_test_families
    assert entries["bijux-proteomics-dev"].flat_test_module_count == 0
    assert entries["bijux-proteomics-dev"].missing_test_families == ("tools",)
    assert entries["bijux-proteomics-dev"].extra_test_families == ("package",)


def test_package_test_tree_mirror_release_guard_has_no_failures() -> None:
    assert validate_package_test_tree_mirror() == ()
