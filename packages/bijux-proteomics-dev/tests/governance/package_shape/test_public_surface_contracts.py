"""Tests for publishable package public surface contracts."""

from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.public_surfaces import (
    default_public_surface_contracts,
    validate_public_surface_contracts,
)


def test_public_surface_contracts_cover_publishable_packages() -> None:
    contracts = default_public_surface_contracts()

    assert [contract.distribution_name for contract in contracts] == [
        "agentic-proteins",
        "bijux-proteomics",
        "bijux-proteomics-core",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
        "proteomics",
        "proteomics-core",
        "proteomics-foundation",
        "proteomics-intelligence",
        "proteomics-knowledge",
        "proteomics-lab",
        "proteomics-runtime",
        "bijux-proteomics-dev",
    ]


def test_public_surface_contracts_validate_supported_import_surfaces() -> None:
    assert validate_public_surface_contracts() == []
