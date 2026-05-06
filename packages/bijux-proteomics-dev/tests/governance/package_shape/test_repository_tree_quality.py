from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.repository_tree_quality import (
    REPOSITORY_TREE_QUALITY_PATH,
    build_repository_tree_quality_report,
    run,
    validate_repository_tree_quality,
)


def test_repository_tree_quality_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_repository_tree_quality_scores_every_workspace_package() -> None:
    report = build_repository_tree_quality_report()
    packages = {package.distribution_name: package for package in report.packages}

    assert REPOSITORY_TREE_QUALITY_PATH.exists()
    assert len(report.packages) == 8
    assert "bijux-proteomics-lab" in packages
    assert "bijux-proteomics-runtime" in packages
    assert packages["bijux-proteomics-lab"].test_tree_mirroring_score == 88.89
    assert packages["bijux-proteomics-lab"].broad_root_import_count == 0
    assert packages["bijux-proteomics-core"].source_owner_family_count >= 5
    assert packages["bijux-proteomics-core"].overall_tree_quality_score >= 50.0
    assert all(package.overall_tree_quality_score > 0.0 for package in report.packages)


def test_repository_tree_quality_release_guard_has_no_failures() -> None:
    assert validate_repository_tree_quality() == ()
