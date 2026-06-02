from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifacts.package_root_hygiene import (
    PackageRootHygieneIssue,
    build_package_root_hygiene_report,
    validate_package_root_hygiene,
)


def test_package_root_hygiene_detects_cache_and_spillover_state(tmp_path: Path) -> None:
    package_root = tmp_path / "packages" / "example-package"
    (package_root / ".pytest_cache").mkdir(parents=True)
    (package_root / ".ruff_cache").mkdir(parents=True)
    (package_root / "coverage.xml").write_text("coverage", encoding="utf-8")

    report = build_package_root_hygiene_report(tmp_path)

    entry = next(item for item in report if item.distribution_name == "example-package")
    assert entry.cache_paths == (
        "packages/example-package/.pytest_cache",
        "packages/example-package/.ruff_cache",
    )
    assert entry.spillover_paths == ("packages/example-package/coverage.xml",)


def test_live_repo_package_roots_are_hygienic() -> None:
    assert validate_package_root_hygiene() == ()


def test_validate_package_root_hygiene_purges_cache_noise_before_reporting(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "packages" / "example-package"
    cache_dir = package_root / ".pytest_cache"
    cache_dir.mkdir(parents=True)
    (package_root / "coverage.xml").write_text("coverage", encoding="utf-8")

    issues = validate_package_root_hygiene(tmp_path)

    assert issues == (
        PackageRootHygieneIssue(
            code="package-root-spillover",
            detail=(
                "example-package still contains forbidden root output at "
                "packages/example-package/coverage.xml"
            ),
        ),
    )
    assert not cache_dir.exists()
