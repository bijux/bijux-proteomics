"""Tests for cross-package shared function signature freeze contracts."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.contracts.cross_package_function_signatures import (
    CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH,
    build_cross_package_function_signature_report,
    find_cross_package_function_signature_entry,
    run,
    validate_cross_package_function_signatures,
)


def test_cross_package_function_signature_report_stays_substantive() -> None:
    report = build_cross_package_function_signature_report()
    assert len(report.entries) >= 200


def test_cross_package_function_signature_report_covers_dia_and_shared_functions() -> (
    None
):
    report = build_cross_package_function_signature_report()

    dia_capability_entry = find_cross_package_function_signature_entry(
        report,
        provider_module="bijux_proteomics.dia",
        function_name="build_dia_capability_matrix",
    )
    assert (
        dia_capability_entry.signature_text
        == "(entries: 'tuple[DiaCapabilityMatrixEntry, ...]') -> 'DiaCapabilityMatrixReport'"
    )
    assert dia_capability_entry.consumer_distributions == (
        "bijux-proteomics-intelligence",
    )

    dia_support_entry = find_cross_package_function_signature_entry(
        report,
        provider_module="bijux_proteomics.dia.benchmarks",
        function_name="build_dia_workflow_scientific_support_report",
    )
    assert dia_support_entry.consumer_distributions == (
        "bijux-proteomics-intelligence",
    )
    assert "imported_precursor_count: 'int'" in dia_support_entry.signature_text
    assert (
        "sample_library_coverage_fraction: 'float | None' = None"
        in dia_support_entry.signature_text
    )

    design_entry = find_cross_package_function_signature_entry(
        report,
        provider_module="bijux_proteomics.io.formats",
        function_name="parse_experimental_design_table",
    )
    assert design_entry.signature_text == "(path: 'Path') -> 'ExperimentalDesignReport'"
    assert design_entry.consumer_distributions == (
        "bijux-proteomics-intelligence",
        "bijux-proteomics-runtime",
    )

    hash_entry = find_cross_package_function_signature_entry(
        report,
        provider_module="bijux_proteomics_foundation",
        function_name="hash_payload",
    )
    assert (
        hash_entry.signature_text
        == "(payload: 'Mapping[str, Any]', *, policy: 'StableHashPolicy | None' = None) -> 'str'"
    )
    assert hash_entry.consumer_distributions == (
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    )


def test_cross_package_function_signature_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_cross_package_function_signatures_detect_signature_drift(
    tmp_path: Path,
) -> None:
    report = build_cross_package_function_signature_report()
    entry = find_cross_package_function_signature_entry(
        report,
        provider_module="bijux_proteomics.dia",
        function_name="build_dia_capability_matrix",
    )
    baseline_text = CROSS_PACKAGE_FUNCTION_SIGNATURES_PATH.read_text(encoding="utf-8")
    stale_path = tmp_path / "cross-package-function-signatures.toml"
    stale_path.write_text(
        baseline_text.replace(
            f'signature_text = "{entry.signature_text}"',
            'signature_text = "(entries: tuple[object, ...]) -> object"',
            1,
        ),
        encoding="utf-8",
    )

    failures = validate_cross_package_function_signatures(
        report, baseline_path=stale_path
    )

    assert failures == (
        "signature drift for bijux_proteomics.dia.build_dia_capability_matrix: "
        "(entries: tuple[object, ...]) -> object -> "
        "(entries: 'tuple[DiaCapabilityMatrixEntry, ...]') -> 'DiaCapabilityMatrixReport'",
    )
