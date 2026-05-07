from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_runtime_doc(name: str) -> str:
    return (
        REPO_ROOT
        / "docs"
        / "09-bijux-proteomics-runtime"
        / name
    ).read_text(encoding="utf-8")


def test_runtime_index_links_to_flagship_run_registry() -> None:
    text = _read_runtime_doc("index.md")

    assert "Flagship Run Registry" in text
    assert "flagship-run-registry" in text


def test_flagship_run_registry_page_names_checked_runtime_artifacts() -> None:
    text = _read_runtime_doc("flagship-run-registry.md")

    assert "# Flagship Run Registry" in text
    assert "runtime_run_registry.json" in text
    assert "cross_family_run_bundle.json" in text
    assert "dda-maxquant-pipeline-corpus" in text
    assert "dia-diann-pipeline-corpus" in text
    assert "lfq-cohort-review-corpus" in text
    assert "multiplex-tmtpro-review-corpus" in text
    assert "ptm-localization-review-corpus" in text
    assert "targeted-transition-review-corpus" in text
    assert "raw-executable review lane over tracked DIA library-conditioned evidence" in text
    assert "raw-executable review lane over tracked targeted QC and follow-up artifacts" in text
