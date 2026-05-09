from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


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
        "build_repository_truth_report()",
        "validate_generated_governance_freshness()",
        "validate_public_language()",
        "workflow_lab_consequence.py",
        "workflow_public_scrutiny.py",
        "validate_ssot_readiness()",
        "canonical-workflow-manifest.toml",
        "scientific-release-workflows.toml",
        "workflows/black_box_reproducibility.py",
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
    assert (
        "benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json"
        in text
    )
    assert "dda-maxquant-pipeline-corpus" in text
    assert "comparator_path:msfragger_imported_dda_review" in text
    assert "runtime flagship rerun gate" in text
    assert "lab-consequence gate" in text
    assert "runtime-execution-boundary.md" in text
    assert "black-box-run-verification.md" in text
    assert "raw-versus-import-execution.md" in text
    assert "runtime-rerun-refusals.md" in text
    assert "flagship-release-candidate.md" in text
    assert "elite-readiness-scorecard.md" in text
    assert "workflow-claim-limits.md" in text
    assert "why-multiplex-stops-at-internal-support.md" in text
    assert "public-artifact-index.md" in text
    assert "public-artifact-role-matrix.md" in text
    assert "validate_workflow_public_scrutiny()" in text


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
    assert "reviews/benchmarks.py" in intelligence_readme
    assert "build_scientific_release_dossier()" in dev_readme
    assert "scientific-release-workflows.toml" in dev_readme
