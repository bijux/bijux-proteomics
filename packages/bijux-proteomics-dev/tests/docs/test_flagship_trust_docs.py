from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_doc(name: str) -> str:
    return (
        REPO_ROOT
        / "docs"
        / "01-bijux-proteomics"
        / "foundation"
        / name
    ).read_text(encoding="utf-8")


def test_flagship_trust_pages_exist_for_all_five_workflow_families() -> None:
    expected_files = (
        "why-trust-dda.md",
        "why-trust-dia.md",
        "why-trust-lfq.md",
        "why-trust-ptm.md",
        "why-trust-targeted.md",
    )
    for name in expected_files:
        text = _read_doc(name)
        assert "# Why Trust" in text
        assert "Current Trust Earned" in text
        assert (
            "What You Should Not Trust Yet" in text
            or "Limits That Stay In Force" in text
        )


def test_dda_trust_page_leads_with_real_public_package_and_runtime_lane() -> None:
    text = _read_doc("why-trust-dda.md")

    assert "outsider_review:dda" in text
    assert "dda-maxquant-pipeline-corpus" in text
    assert "public_benchmark_packages/dda_reviewable_run/package_manifest.json" in text
    assert "search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv" in text


def test_non_dda_trust_pages_keep_weaker_posture_visible() -> None:
    dia = _read_doc("why-trust-dia.md")
    lfq = _read_doc("why-trust-lfq.md")
    ptm = _read_doc("why-trust-ptm.md")
    targeted = _read_doc("why-trust-targeted.md")

    assert "external_reproduction_package" in dia
    assert "import_only" in dia
    assert "do_not_recommend" in lfq
    assert "public claim support is `refused`" in ptm
    assert "no flagship runtime truth row is published for targeted yet" in targeted
