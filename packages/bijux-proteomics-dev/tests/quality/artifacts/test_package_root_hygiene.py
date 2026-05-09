from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.artifacts.package_root_hygiene import (
    build_package_root_hygiene_report,
    validate_package_root_hygiene,
)


def test_package_root_hygiene_detects_cache_and_spillover_state(tmp_path: Path) -> None:
    package_root = tmp_path / "packages" / "example-package"
    (package_root / ".pytest_cache").mkdir(parents=True)
    (package_root / "tests" / "__pycache__").mkdir(parents=True)
    (package_root / "coverage.xml").write_text("coverage", encoding="utf-8")

    report = build_package_root_hygiene_report(tmp_path)

    entry = next(item for item in report if item.distribution_name == "example-package")
    assert entry.cache_paths == (
        "packages/example-package/.pytest_cache",
        "packages/example-package/tests/__pycache__",
    )
    assert entry.spillover_paths == ("packages/example-package/coverage.xml",)


def test_live_repo_package_roots_are_hygienic() -> None:
    assert validate_package_root_hygiene() == ()
