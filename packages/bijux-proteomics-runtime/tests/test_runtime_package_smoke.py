import bijux_proteomics_runtime


def test_runtime_package_imports() -> None:
    assert bijux_proteomics_runtime is not None


def test_runtime_package_exports_report_convenience_symbols() -> None:
    assert "Report" in bijux_proteomics_runtime.__all__
    assert "Metrics" in bijux_proteomics_runtime.__all__
    assert bijux_proteomics_runtime.Report is not None
    assert bijux_proteomics_runtime.Metrics is not None


def test_runtime_package_exports_confidence_convenience_symbol() -> None:
    assert "low_confidence_segments" in bijux_proteomics_runtime.__all__
    assert bijux_proteomics_runtime.low_confidence_segments is not None
