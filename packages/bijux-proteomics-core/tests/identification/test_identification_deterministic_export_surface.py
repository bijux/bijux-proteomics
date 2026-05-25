# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.comet_import import (
    build_comet_import_report,
    render_comet_canonical_psm_tsv,
    render_comet_psm_tsv,
)
from bijux_proteomics.identification.diann_import import (
    build_diann_import_report,
    render_diann_precursor_tsv,
    render_diann_protein_group_tsv,
    render_diann_rejected_row_tsv,
)
from bijux_proteomics.identification.maxquant_import import (
    build_maxquant_import_report,
    render_maxquant_lfq_candidate_tsv,
    render_maxquant_peptide_tsv,
    render_maxquant_protein_group_tsv,
)
from bijux_proteomics.identification.fragpipe_import import (
    build_fragpipe_import_report,
    render_fragpipe_canonical_psm_tsv,
    render_fragpipe_open_search_evidence_tsv,
    render_fragpipe_peptide_tsv,
    render_fragpipe_protein_quantity_tsv,
    render_fragpipe_protein_tsv,
    render_fragpipe_psm_tsv,
)
from bijux_proteomics.identification.generic_psm_mapper import (
    build_generic_psm_mapper_report,
    render_generic_psm_mapper_tsv,
    render_generic_psm_rejected_row_tsv,
)
from bijux_proteomics.identification.openms_import import (
    build_openms_import_report,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
    render_openms_rejected_feature_tsv,
)
from bijux_proteomics.identification.sage_import import (
    build_sage_import_report,
    render_sage_canonical_psm_tsv,
    render_sage_psm_tsv,
)
from bijux_proteomics.identification.spectronaut_import import (
    build_spectronaut_import_report,
    render_spectronaut_precursor_quantity_tsv,
    render_spectronaut_precursor_tsv,
    render_spectronaut_protein_group_quantity_tsv,
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
        quant_tsv_path=root / "combined_quant.tsv",
    )

    assert render_fragpipe_canonical_psm_tsv(
        report.canonical_psms
    ) == render_fragpipe_canonical_psm_tsv(_reversed_rows(report.canonical_psms))
    assert render_fragpipe_psm_tsv(report.psm_rows) == render_fragpipe_psm_tsv(
        _reversed_rows(report.psm_rows)
    )
    assert render_fragpipe_peptide_tsv(
        report.peptide_rows
    ) == render_fragpipe_peptide_tsv(_reversed_rows(report.peptide_rows))
    assert render_fragpipe_protein_tsv(
        report.protein_rows
    ) == render_fragpipe_protein_tsv(_reversed_rows(report.protein_rows))
    assert render_fragpipe_open_search_evidence_tsv(
        report.open_search_evidence
    ) == render_fragpipe_open_search_evidence_tsv(
        _reversed_rows(report.open_search_evidence)
    )
    assert render_fragpipe_protein_quantity_tsv(
        report.protein_quantity_rows
    ) == render_fragpipe_protein_quantity_tsv(
        _reversed_rows(report.protein_quantity_rows)
    )


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

    assert render_comet_canonical_psm_tsv(
        comet_report.canonical_psms
    ) == render_comet_canonical_psm_tsv(_reversed_rows(comet_report.canonical_psms))
    assert render_comet_psm_tsv(report_rows := comet_report.psm_rows) == render_comet_psm_tsv(
        _reversed_rows(report_rows)
    )
    assert render_sage_canonical_psm_tsv(
        sage_report.canonical_psms
    ) == render_sage_canonical_psm_tsv(_reversed_rows(sage_report.canonical_psms))
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
    assert render_openms_rejected_feature_tsv(
        report.rejected_feature_rows
    ) == render_openms_rejected_feature_tsv(_reversed_rows(report.rejected_feature_rows))


def test_generic_mapper_export_renderers_ignore_input_row_order(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent / "fixtures" / "search_adapters"
    invalid_input = tmp_path / "generic_mapper_invalid.tsv"
    invalid_input.write_text(
        "\n".join(
            (
                "run_name\tscan_ref\tsequence_text\tmodified_sequence\tz\tstate_score\tprecursor_intensity\tqvalue\taccessions\tdecoy_state\tcontaminant_state\tinstrument\tanalyst_note",
                "run_A\tgeneric-1001\tPESTIDE\tPES[Phospho]TIDE\t2\t55.0\t125000\t0.002\tP12345\ttarget\tfalse\torbitrap\tstable",
                "run_B\tgeneric-1002\tBROKEN\tBROKEN\tbad\t12.0\t4300\t0.05\tCON__P54321\tdecoy\tcontaminant\ttof\treview",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_generic_psm_mapper_report(
        invalid_input,
        mapping_path=root / "generic_mapper_mapping.yaml",
    )

    assert render_generic_psm_mapper_tsv(
        report.mapped_rows
    ) == render_generic_psm_mapper_tsv(_reversed_rows(report.mapped_rows))
    assert render_generic_psm_rejected_row_tsv(
        report.rejected_rows
    ) == render_generic_psm_rejected_row_tsv(_reversed_rows(report.rejected_rows))


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


def test_diann_rejected_row_renderer_ignores_input_row_order(tmp_path: Path) -> None:
    report_path = tmp_path / "diann_invalid.tsv"
    report_path.write_text(
        "\n".join(
            (
                "Precursor.Id\tStripped.Sequence\tModified.Sequence\tPrecursor.Charge\tQ.Value\tProtein.Group\tProtein.Ids\tRun\tSample\tPrecursor.Quantity\tPG.Quantity\tDecoy",
                "raw_A_PEPTIDE_2\tPEPTIDE\tPEPTIDE\t2\t0.01\tPG001\tP11111\traw_A\tsample_A\t50\t1000\t0",
                "raw_B_BADQ_2\tBADQ\tBADQ\t2\t1.2\tPG002\tP22222\traw_B\tsample_B\t120\t2000\t0",
                "raw_C_NEGQTY_2\tNEGQTY\tNEGQTY\t2\t0.02\tPG003\tP33333\traw_C\tsample_C\t-5\t1000\t0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_diann_import_report(report_path)

    assert render_diann_rejected_row_tsv(
        report.rejected_rows
    ) == render_diann_rejected_row_tsv(_reversed_rows(report.rejected_rows))


def test_maxquant_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("maxquant")
    report = build_maxquant_import_report(
        root / "evidence.txt",
        peptides_txt_path=root / "peptides.txt",
        protein_groups_txt_path=root / "proteinGroups.txt",
        config_path=root / "maxquant_settings.txt",
    )

    assert render_maxquant_peptide_tsv(
        report.peptide_rows
    ) == render_maxquant_peptide_tsv(_reversed_rows(report.peptide_rows))
    assert render_maxquant_protein_group_tsv(
        report.protein_group_rows
    ) == render_maxquant_protein_group_tsv(_reversed_rows(report.protein_group_rows))
    assert render_maxquant_lfq_candidate_tsv(
        report.lfq_matrix_candidates
    ) == render_maxquant_lfq_candidate_tsv(
        _reversed_rows(report.lfq_matrix_candidates)
    )


def test_spectronaut_export_renderers_ignore_input_row_order() -> None:
    root = _bundle_root("spectronaut")
    report = build_spectronaut_import_report(
        root / "spectronaut_report.tsv",
        config_path=root / "spectronaut_settings.txt",
    )

    assert render_spectronaut_precursor_tsv(
        report.precursor_rows
    ) == render_spectronaut_precursor_tsv(_reversed_rows(report.precursor_rows))
    assert render_spectronaut_precursor_quantity_tsv(
        report.precursor_quantity_rows
    ) == render_spectronaut_precursor_quantity_tsv(
        _reversed_rows(report.precursor_quantity_rows)
    )
    assert render_spectronaut_protein_group_tsv(
        report.protein_group_rows
    ) == render_spectronaut_protein_group_tsv(
        _reversed_rows(report.protein_group_rows)
    )
    assert render_spectronaut_protein_group_quantity_tsv(
        report.protein_group_quantity_rows
    ) == render_spectronaut_protein_group_quantity_tsv(
        _reversed_rows(report.protein_group_quantity_rows)
    )
