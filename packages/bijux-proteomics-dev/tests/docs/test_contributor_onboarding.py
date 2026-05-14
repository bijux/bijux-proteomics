from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.docs.contributor_onboarding import (
    ONBOARDING_PATH,
    build_contributor_onboarding_entries,
    run,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_contributor_onboarding_generator_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_contributor_onboarding_covers_all_workspace_packages() -> None:
    entries = build_contributor_onboarding_entries(REPO_ROOT)
    docs = {entry.package_name: entry.docs_root for entry in entries}

    assert len(entries) == 16
    assert docs["bijux-proteomics-dev"] == (
        "docs/08-bijux-proteomics-maintain/bijux-proteomics-dev"
    )
    assert docs["bijux-proteomics-runtime"] == "docs/09-bijux-proteomics-runtime"
    page = ONBOARDING_PATH.read_text(encoding="utf-8")
    assert "Package Contributor Onboarding" in page
    assert "`packages/bijux-proteomics-core/tests`" in page
