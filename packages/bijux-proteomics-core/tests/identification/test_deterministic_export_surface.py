# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.comet_import import (
    build_comet_import_report,
    render_comet_psm_tsv,
)
from bijux_proteomics.identification.diann_import import (
    build_diann_import_report,
    render_diann_precursor_tsv,
    render_diann_protein_group_tsv,
)
from bijux_proteomics.identification.fragpipe_import import (
    build_fragpipe_import_report,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
)
from bijux_proteomics.identification.openms_import import (
    build_openms_import_report,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
)
from bijux_proteomics.identification.sage_import import (
    build_sage_import_report,
    render_sage_psm_tsv,
)
from bijux_proteomics.identification.spectronaut_import import (
    build_spectronaut_import_report,
    render_spectronaut_precursor_tsv,
    render_spectronaut_protein_group_tsv,
)


def _bundle_root(engine_name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / engine_name
    )


def _reversed_rows(rows: tuple[object, ...]) -> tuple[object, ...]:
    return tuple(reversed(rows))


def test_fragpipe_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("fragpipe")
    report = build_fragpipe_import_report(
        root / "psm.tsv",
        peptide_tsv_path=root / "combined_peptide.tsv",
        protein_tsv_path=root / "combined_protein.tsv",
    )

    assert render_fragpipe_psm_tsv(report.psm_rows) == render_fragpipe_psm_tsv(
        _reversed_rows(report.psm_rows)
    )
    assert render_fragpipe_peptide_tsv(
        report.peptide_rows
    ) == render_fragpipe_peptide_tsv(_reversed_rows(report.peptide_rows))
    assert render_fragpipe_protein_tsv(
        report.protein_rows
    ) == render_fragpipe_protein_tsv(_reversed_rows(report.protein_rows))


def test_comet_and_sage_psm_exports_ignore_input_row_order() -> None:
    comet_root = _bundle_root("comet")
    comet_report = build_comet_import_report(
        comet_root / "comet_psm.tsv",
        config_path=comet_root / "comet.params",
    )
    sage_root = _bundle_root("sage")
    sage_report = build_sage_import_report(
        sage_root / "sage_psm.tsv",
        config_path=sage_root / "sage_search.json",
    )

    assert render_comet_psm_tsv(report_rows := comet_report.psm_rows) == render_comet_psm_tsv(
        _reversed_rows(report_rows)
    )
    assert render_sage_psm_tsv(report_rows := sage_report.psm_rows) == render_sage_psm_tsv(
        _reversed_rows(report_rows)
    )


def test_openms_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("openms")
    report = build_openms_import_report(
        root / "openms.idxml",
        feature_table_path=root / "openms_features.tsv",
    )

    assert render_openms_psm_tsv(report.psm_rows) == render_openms_psm_tsv(
        _reversed_rows(report.psm_rows)
    )
    assert render_openms_protein_tsv(
        report.protein_rows
    ) == render_openms_protein_tsv(_reversed_rows(report.protein_rows))
    assert render_openms_feature_tsv(
        report.feature_rows
    ) == render_openms_feature_tsv(_reversed_rows(report.feature_rows))


def test_diann_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("diann")
    report = build_diann_import_report(
        root / "diann_report.tsv",
        config_path=root / "diann_config.json",
    )

    assert render_diann_precursor_tsv(
        report.precursor_rows
    ) == render_diann_precursor_tsv(_reversed_rows(report.precursor_rows))
    assert render_diann_protein_group_tsv(
        report.protein_group_rows
    ) == render_diann_protein_group_tsv(_reversed_rows(report.protein_group_rows))


def test_spectronaut_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("spectronaut")
    report = build_spectronaut_import_report(
        root / "spectronaut_report.tsv",
        config_path=root / "spectronaut_settings.txt",
    )

    assert render_spectronaut_precursor_tsv(
        report.precursor_rows
    ) == render_spectronaut_precursor_tsv(_reversed_rows(report.precursor_rows))
    assert render_spectronaut_protein_group_tsv(
        report.protein_group_rows
    ) == render_spectronaut_protein_group_tsv(
        _reversed_rows(report.protein_group_rows)
    )
