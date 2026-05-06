from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.package_coupling import (
    build_package_coupling_report,
    render_package_coupling_summary,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_package_coupling_report_surfaces_current_hotspots() -> None:
    report = build_package_coupling_report(REPO_ROOT)
    by_package = {row.package_name: row for row in report}

    assert report[0].package_name == "bijux-proteomics-runtime"
    assert by_package["bijux-proteomics-foundation"].pressure_level == "watch"
    assert by_package["agentic-proteins"].direct_dependency_count == 6
    assert by_package["bijux-proteomics-knowledge"].reverse_dependency_count == 4


def test_package_coupling_summary_renders_tsv_like_output() -> None:
    summary = render_package_coupling_summary(REPO_ROOT)

    assert summary.startswith("package_name\tpressure\tscore")
    assert "bijux-proteomics-runtime\televated" in summary
    assert "bijux-proteomics-dev\tstable" in summary
    assert "current coupling stays within the normal package budget" in summary
