from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.public_symbol_ledger import (
    PUBLIC_SYMBOL_LEDGER_PATH,
    build_public_symbol_ledger_report,
    run,
    validate_public_symbol_ledger,
)


def test_public_symbol_ledger_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_public_symbol_ledger_maps_exports_to_owner_modules_and_tests() -> None:
    report = build_public_symbol_ledger_report()
    by_symbol = {
        (entry.distribution_name, entry.symbol_name): entry for entry in report.entries
    }

    foundation_symbol = by_symbol[
        ("bijux-proteomics-foundation", "DocumentSchema")
    ]
    runtime_symbol = by_symbol[("bijux-proteomics-runtime", "RunManager")]
    intelligence_symbol = by_symbol[("bijux-proteomics-intelligence", "candidates")]

    assert PUBLIC_SYMBOL_LEDGER_PATH.exists()
    assert foundation_symbol.owner_module_name.startswith(
        "bijux_proteomics_foundation."
    )
    assert foundation_symbol.owner_test_paths
    assert runtime_symbol.owner_module_path.endswith(".py")
    assert runtime_symbol.owner_test_paths
    assert intelligence_symbol.owner_module_name == "bijux_proteomics_intelligence.candidates"


def test_public_symbol_ledger_requires_named_owner_modules_and_tests() -> None:
    assert validate_public_symbol_ledger() == ()
