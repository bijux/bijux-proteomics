from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.public_api_snapshots import (
    build_public_api_snapshot_packages,
    run,
    validate_public_api_snapshots,
)


def test_public_api_snapshots_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_public_api_snapshots_cover_all_canonical_product_packages() -> None:
    packages = build_public_api_snapshot_packages()

    assert tuple(package.distribution_name for package in packages) == (
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    )
    assert all(package.entries for package in packages)


def test_public_api_snapshots_have_no_validation_failures() -> None:
    assert validate_public_api_snapshots() == ()
