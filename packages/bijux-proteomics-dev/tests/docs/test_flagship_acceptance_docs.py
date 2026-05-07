from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_doc() -> str:
    return (
        REPO_ROOT
        / "docs"
        / "04-bijux-proteomics-core"
        / "foundation"
        / "flagship-acceptance-bars.md"
    ).read_text(encoding="utf-8")


def test_flagship_acceptance_doc_lists_all_six_family_sheets_and_dashboard_surfaces() -> None:
    text = _read_doc()

    assert "# Flagship Acceptance Bars" in text
    for file_name in (
        "dda_acceptance_sheet.json",
        "dia_acceptance_sheet.json",
        "lfq_acceptance_sheet.json",
        "multiplex_acceptance_sheet.json",
        "ptm_acceptance_sheet.json",
        "targeted_acceptance_sheet.json",
        "acceptance_dashboard.json",
        "benchmark_history_ledger.json",
        "acceptance_rationale_dossier.json",
    ):
        assert f"`{file_name}`" in text


def test_flagship_acceptance_doc_keeps_multiplex_failure_and_refresh_command_visible() -> None:
    text = _read_doc()

    assert "`multiplex` remains `internal_support_only`" in text
    assert "flagship_acceptance_assets refresh" in text
    assert "Flagship Challenge Corpus Catalog" in text


def test_foundation_index_points_to_flagship_acceptance_bars() -> None:
    text = (
        REPO_ROOT / "docs" / "04-bijux-proteomics-core" / "foundation" / "index.md"
    ).read_text(encoding="utf-8")

    assert "Flagship Acceptance Bars" in text
