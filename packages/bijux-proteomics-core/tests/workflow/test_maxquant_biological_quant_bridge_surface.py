# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.maxquant_import import (
    build_maxquant_import_report,
    build_maxquant_lfq_matrix_candidates,
)
from bijux_proteomics.quantification import MissingValueKind
from bijux_proteomics.workflow.maxquant_biological_workflow import (
    build_label_free_quant_table_from_maxquant_lfq_candidates,
    build_label_free_quant_table_from_maxquant_protein_groups,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_build_label_free_quant_table_from_maxquant_protein_groups_preserves_members_and_sample_intensities() -> (
    None
):
    import_report = build_maxquant_import_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
    )

    table = build_label_free_quant_table_from_maxquant_protein_groups(
        tuple(
            row
            for row in import_report.protein_group_rows
            if row.protein_ids
            in {
                ("P04637",),
                ("Q9Y243",),
            }
        ),
        peptide_rows=import_report.peptide_rows,
    )

    assert table.sample_ids == ("C1", "C2", "C3", "T1", "T2", "T3")
    assert table.entity_ids == ("P04637", "Q9Y243")
    assert table.entity_protein_refs["P04637"] == ("P04637",)
    assert table.entity_member_peptides["P04637"] == ("PEPAAA",)
    assert table.entity_member_peptides["Q9Y243"] == ("PEPBBB",)
    c1_value = next(
        value
        for value in table.values
        if value.entity_id == "P04637" and value.sample_id == "C1"
    )
    t1_value = next(
        value
        for value in table.values
        if value.entity_id == "Q9Y243" and value.sample_id == "T1"
    )
    assert c1_value.abundance == 200.0
    assert c1_value.missing_value_kind is MissingValueKind.OBSERVED
    assert t1_value.abundance == 200.0
    assert t1_value.missing_value_kind is MissingValueKind.OBSERVED


def test_build_label_free_quant_table_from_maxquant_lfq_candidates_preserves_flags_and_members() -> (
    None
):
    import_report = build_maxquant_import_report(
        _bundle_fixture("evidence.txt"),
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
    )

    candidates = build_maxquant_lfq_matrix_candidates(
        tuple(
            row
            for row in import_report.protein_group_rows
            if row.protein_ids
            in {
                ("P04637",),
                ("CON__KRT1",),
            }
        ),
        peptide_rows=import_report.peptide_rows,
    )
    table = build_label_free_quant_table_from_maxquant_lfq_candidates(candidates)

    assert candidates[0].member_peptides == ("PEPAAA",)
    assert candidates[1].contaminant_flag is True
    assert table.entity_member_peptides[candidates[0].entity_id] == ("PEPAAA",)
