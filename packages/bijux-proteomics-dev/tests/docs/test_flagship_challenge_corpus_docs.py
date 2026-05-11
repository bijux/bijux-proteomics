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
        / "flagship-challenge-corpus-catalog.md"
    ).read_text(encoding="utf-8")


def test_flagship_challenge_corpus_doc_lists_holdout_and_perturbation_families() -> (
    None
):
    text = _read_doc()

    assert "# Flagship Challenge Corpus Catalog" in text
    for root_name in (
        "dda_blinded_holdout",
        "dia_blinded_holdout",
        "lfq_blinded_holdout",
        "ptm_blinded_holdout",
        "dda_calibration_decoy_perturbation",
        "dia_library_dropout_perturbation",
        "lfq_missingness_drift_perturbation",
        "multiplex_reference_bleed_perturbation",
        "ptm_ambiguity_occupancy_perturbation",
        "targeted_interference_carryover_perturbation",
    ):
        assert f"`{root_name}`" in text


def test_flagship_challenge_corpus_doc_points_to_machine_readable_registry() -> None:
    text = _read_doc()

    assert "challenge_registry.json" in text
    assert "challenge_manifest.json" in text
    assert "perturbation_report.json" in text
    assert "blinded_holdout_report.json" in text
    assert "benchmark-assets/flagship-challenge-corpora" in text


def test_flagship_challenge_corpus_doc_keeps_current_coverage_limits_explicit() -> None:
    text = _read_doc()

    assert "`multiplex` and `targeted` do not yet have blinded holdout roots" in text
    assert "Flagship Public Benchmark Catalog" in text
    assert "Flagship Benchmark Assets" in text
