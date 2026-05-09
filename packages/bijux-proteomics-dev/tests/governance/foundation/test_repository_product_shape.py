from __future__ import annotations

from bijux_proteomics_dev.governance.foundation.repository_product_shape import (
    REPOSITORY_PRODUCT_SHAPE_PATH,
    build_repository_product_shape_report,
    run,
    validate_repository_product_shape,
)


def test_repository_product_shape_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_repository_product_shape_covers_lifecycle_and_package_roles() -> None:
    report = build_repository_product_shape_report()
    by_package = {entry.distribution_name: entry for entry in report.packages}
    by_stage = {entry.stage_id: entry for entry in report.stages}
    by_handoff = {entry.handoff_class: entry for entry in report.handoffs}

    assert REPOSITORY_PRODUCT_SHAPE_PATH.exists()
    assert tuple(by_stage) == (
        "shared-contracts",
        "benchmark-intake",
        "runtime-execution",
        "scientific-review",
        "recommendation-posture",
        "lab-consequence",
    )
    assert by_stage["runtime-execution"].owner_package == "bijux-proteomics-runtime"
    assert by_stage["scientific-review"].owner_package == "bijux-proteomics-knowledge"
    assert by_stage["lab-consequence"].handoff_class == "lab-consequence-record"
    assert (
        by_handoff["runtime-run-bundle"].consumer_packages
        == (
            "bijux-proteomics-knowledge",
            "bijux-proteomics-intelligence",
            "bijux-proteomics-lab",
        )
    )
    assert by_package["agentic-proteins"].role_kind == "compatibility"
    assert (
        by_package["agentic-proteins"].role_summary
        == "legacy compatibility bridge for runtime entrypoints and imports"
    )
    assert by_package["bijux-proteomics-core"].owned_handoff_classes == (
        "benchmark-asset-bundle",
    )
    assert by_package["bijux-proteomics-runtime"].owned_handoff_classes == (
        "runtime-run-bundle",
    )


def test_repository_product_shape_has_no_live_validation_failures() -> None:
    assert validate_repository_product_shape() == ()
