# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

from bijux_proteomics import io

formats = importlib.import_module("bijux_proteomics.io.formats")
spectra = importlib.import_module("bijux_proteomics.io.spectra")
tables = importlib.import_module("bijux_proteomics.io.tables")
raw = importlib.import_module("bijux_proteomics.io.raw")
chromatography = importlib.import_module("bijux_proteomics.io.chromatography")


_WRAPPER_MODULES = (
    "io/format_validation.py",
    "io/ingestion.py",
    "io/input_integrity.py",
    "io/spectral_library.py",
    "io/spectral_library_intensity_agreement.py",
    "io/stable_outputs.py",
    "io/target_panel.py",
    "io/transition_table.py",
    "io/mgf_streaming.py",
    "io/mzml_reader.py",
    "io/noise.py",
    "io/deisotoping.py",
    "io/run_qc.py",
    "io/chimeric_spectrum.py",
    "io/spectrum_entropy.py",
    "io/spectrum_peak_matching.py",
    "io/precursor_validation.py",
    "io/xic_extraction.py",
    "io/chromatographic_peak_picking.py",
    "io/retention_time_alignment.py",
    "io/chromatographic_evidence.py",
    "io/dia_fragment_coelution.py",
    "io/fragment_ratio_stability.py",
    "io/precursor_isotope_fit.py",
    "io/raw_signal_evidence_cards.py",
)


def _core_src_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"


def test_io_subpackages_export_representative_owner_surfaces() -> None:
    assert hasattr(formats, "parse_experimental_design_table")
    assert hasattr(formats, "parse_mzml")
    assert hasattr(spectra, "SpectrumModel")
    assert hasattr(spectra, "score_chimeric_spectra")
    assert hasattr(tables, "DelimitedLookupJoinSpec")
    assert hasattr(tables, "iter_streaming_lookup_join")
    assert hasattr(tables, "iter_delimited_row_chunks")
    assert hasattr(tables, "parse_target_panel_table")
    assert hasattr(tables, "parse_xic_target_table")
    assert hasattr(raw, "parse_mzml")
    assert hasattr(raw, "extract_mzml_xic_traces")
    assert hasattr(raw, "extract_mzml_precursor_isotope_fit")
    assert hasattr(chromatography, "extract_xic")
    assert hasattr(chromatography, "pick_chromatographic_peaks")
    assert hasattr(chromatography, "align_chromatographic_peak_retention_times")
    assert hasattr(chromatography, "score_dia_fragment_trace_coelution")


def test_io_root_wrappers_stay_compatibility_only() -> None:
    root = _core_src_root()
    for relative_path in _WRAPPER_MODULES:
        path = root / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        body = tree.body
        assert body, f"{relative_path} should not be empty"
        assert isinstance(body[0], ast.Expr)
        for node in body[1:]:
            assert isinstance(
                node,
                ast.ImportFrom,
            ), f"{relative_path} should stay a thin compatibility facade"


def test_io_root_and_subpackage_surfaces_share_owner_functions() -> None:
    assert io.parse_experimental_design_table is formats.parse_experimental_design_table
    assert io.SpectrumModel is spectra.SpectrumModel
    assert io.parse_target_panel_table is tables.parse_target_panel_table
    assert io.extract_mzml_xic_traces is raw.extract_mzml_xic_traces
    assert io.extract_xic is chromatography.extract_xic
    assert (
        io.score_dia_fragment_ratio_stability
        is chromatography.score_dia_fragment_ratio_stability
    )


def test_io_canonical_signal_algorithms_accept_typed_records_not_paths() -> None:
    typed_algorithms = (
        chromatography.extract_xic,
        chromatography.pick_chromatographic_peaks,
        chromatography.score_chromatographic_evidence,
        chromatography.align_chromatographic_peak_retention_times,
        chromatography.score_dia_fragment_trace_coelution,
        chromatography.score_dia_fragment_ratio_stability,
        raw.build_precursor_isotope_fit_report,
        raw.build_raw_signal_evidence_card_report,
    )

    for function in typed_algorithms:
        signature = inspect.signature(function)
        for parameter in signature.parameters.values():
            assert not parameter.name.endswith("_path")
            annotation = parameter.annotation
            if annotation is inspect._empty:
                continue
            assert "Path" not in repr(annotation)
