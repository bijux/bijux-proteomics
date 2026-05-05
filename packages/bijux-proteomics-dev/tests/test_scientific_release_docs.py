from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_release_support_docs_name_the_scientific_release_dossier() -> None:
    doc_path = (
        REPO_ROOT
        / "docs"
        / "08-bijux-proteomics-maintain"
        / "bijux-proteomics-dev"
        / "release-support.md"
    )
    text = doc_path.read_text(encoding="utf-8")

    expected_bits = [
        "build_scientific_release_dossier()",
        "validate_ssot_readiness()",
        "scientific-release-workflows.toml",
        "package-substance.md",
        "`dda`",
        "`dia`",
        "`ptm`",
        "`lfq`",
        "`multiplex`",
        "`targeted`",
    ]
    missing = [bit for bit in expected_bits if bit not in text]
    assert not missing, (
        f"missing scientific release dossier guidance in {doc_path}: {missing}"
    )


def test_readmes_point_reviewers_to_benchmark_backed_scope() -> None:
    intelligence_readme = (
        REPO_ROOT / "packages" / "bijux-proteomics-intelligence" / "README.md"
    ).read_text(encoding="utf-8")
    dev_readme = (
        REPO_ROOT / "packages" / "bijux-proteomics-dev" / "README.md"
    ).read_text(encoding="utf-8")

    assert (
        "benchmark-backed review outputs for `dda`, `dia`, `ptm`,"
        in intelligence_readme
    )
    assert "`lfq`, and `multiplex`" in intelligence_readme
    assert "benchmark_reviews.py" in intelligence_readme
    assert "build_scientific_release_dossier()" in dev_readme
    assert "scientific-release-workflows.toml" in dev_readme
