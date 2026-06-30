from __future__ import annotations

import pytest

from bijux_proteomics_dev.release.governance.release_readiness_matrix import (
    RELEASE_READINESS_MATRIX_PATH,
    build_release_readiness_matrix,
    run,
    validate_release_readiness_matrix,
)

pytestmark = pytest.mark.slow


def test_release_readiness_matrix_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_release_readiness_matrix_covers_hostile_review_categories() -> None:
    matrix = build_release_readiness_matrix()
    by_id = {category.category_id: category for category in matrix.categories}

    assert RELEASE_READINESS_MATRIX_PATH.exists()
    assert tuple(by_id) == (
        "workflow-family-product-evidence",
        "black-box-rerunability",
        "benchmark-asset-quality",
        "docs-clarity",
        "package-boundary-stability",
        "artifact-hygiene",
        "consequence-realism",
    )
    assert not all(category.ready for category in matrix.categories)
    assert (
        "docs/01-bijux-proteomics/foundation/release-readiness-matrix.md"
        in by_id["docs-clarity"].evidence_paths
    )
    assert (
        "configs/package-governance/repository-product-shape.toml"
        in by_id["package-boundary-stability"].evidence_paths
    )
    assert (
        "docs/09-bijux-proteomics-runtime/black-box-benchmark-dashboard.md"
        in by_id["black-box-rerunability"].evidence_paths
    )
    assert (
        "docs/09-bijux-proteomics-runtime/runtime-execution-boundary.md"
        in by_id["black-box-rerunability"].evidence_paths
    )
    assert (
        "docs/04-bijux-proteomics-core/foundation/benchmark-freshness-review.md"
        in by_id["benchmark-asset-quality"].evidence_paths
    )
    assert (
        "configs/package-governance/repository-drift-audit.toml"
        in by_id["artifact-hygiene"].evidence_paths
    )
    assert (
        "docs/01-bijux-proteomics/foundation/workflow-consequence-maps.md"
        in by_id["consequence-realism"].evidence_paths
    )
    assert (
        "docs/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook.md"
        in by_id["consequence-realism"].evidence_paths
    )


def test_release_readiness_matrix_has_no_internal_consistency_failures() -> None:
    assert validate_release_readiness_matrix() == ()


def test_release_readiness_matrix_keeps_blockers_human_readable() -> None:
    matrix = build_release_readiness_matrix()

    for category in matrix.categories:
        for code, detail in zip(
            category.blocker_codes, category.blocker_details, strict=True
        ):
            assert code
            assert detail
