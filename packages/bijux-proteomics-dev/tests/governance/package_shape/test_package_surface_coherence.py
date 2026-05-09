from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_surface_coherence import (
    PACKAGE_SURFACE_COHERENCE_PATH,
    build_package_surface_coherence_report,
    run,
    validate_package_surface_coherence,
)


def test_package_surface_coherence_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_surface_coherence_report_tracks_all_real_product_packages() -> None:
    report = build_package_surface_coherence_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert PACKAGE_SURFACE_COHERENCE_PATH.exists()
    assert tuple(by_package) == (
        "bijux-proteomics-foundation",
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    )
    assert by_package["bijux-proteomics-foundation"].allowed_outbound_edges == ()
    assert "DigestPolicy" in by_package["bijux-proteomics-core"].public_surface_names
    assert "reviews" in by_package["bijux-proteomics-intelligence"].public_surface_names
    assert "EvidenceBundle" in by_package["bijux-proteomics-knowledge"].public_surface_names
    assert (
        "execution orchestration or runtime policy"
        in by_package["bijux-proteomics-lab"].excluded_responsibilities
    )
    assert "RunManager" in by_package["bijux-proteomics-runtime"].public_surface_names


def test_package_surface_coherence_has_no_live_failures() -> None:
    assert validate_package_surface_coherence() == ()
