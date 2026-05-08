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
    assert (
        "benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json"
        in text
    )
    assert (
        "benchmark-assets/flagship-public-packages/dda_cross_engine_review_package/cross_package_generalization.json"
        in text
    )


def test_trust_pages_require_paired_package_generalization_links() -> None:
    expected_links = {
        "why-trust-dda.md": "dda_cross_engine_review_package/cross_package_generalization.json",
        "why-trust-dia.md": "dia_matrix_shift_review_package/cross_package_generalization.json",
        "why-trust-lfq.md": "lfq_sparse_contrast_review_package/cross_package_generalization.json",
        "why-trust-ptm.md": "ptm_ambiguity_stress_review_package/cross_package_generalization.json",
        "why-trust-targeted.md": "targeted_carryover_review_package/cross_package_generalization.json",
    }

    for name, expected_path in expected_links.items():
        text = _read_doc(name)
        assert expected_path in text
        assert "two public" in text or "companion" in text


def test_non_dda_trust_pages_keep_bounded_posture_visible() -> None:
    dia = _read_doc("why-trust-dia.md")
    lfq = _read_doc("why-trust-lfq.md")
    ptm = _read_doc("why-trust-ptm.md")
    targeted = _read_doc("why-trust-targeted.md")

    assert "external_reproduction_package" in dia
    assert "raw_executable" in dia
    assert "`0.83`" in dia
    assert "recommend_with_downgrade" in lfq
    assert "lfq-cohort-review-corpus" in lfq
    assert "`0.84`" in lfq
    assert "public claim support is `advisory`" in ptm
    assert "ptm-localization-review-corpus" in ptm
    assert "`0.8`" in ptm
    assert "targeted-transition-review-corpus" in targeted
    assert "public claim support is `advisory`" in targeted
    assert "raw_executable" in targeted
    assert "`0.87`" in targeted


def test_trust_and_boundary_pages_link_to_claim_grounding_and_literature_audits() -> (
    None
):
    docs = (
        "why-trust-dda.md",
        "why-trust-dia.md",
        "why-trust-lfq.md",
        "why-trust-ptm.md",
        "why-trust-targeted.md",
        "multiplex-authority-boundary.md",
    )

    for name in docs:
        text = _read_doc(name)
        assert "Evidence Grounding" in text
        assert "workflow-claim-grounding" in text
        assert "workflow-literature-audits" in text
