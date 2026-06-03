# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics._scientific_tables import (
    ScientificTableValidationContext,
    ScientificTableValidationError,
    build_contrast_table_schema,
    build_diann_report_schema,
    build_experimental_design_schema,
    build_maxquant_peptides_schema,
    build_maxquant_protein_groups_schema,
    build_psm_table_schema,
    build_ptm_evidence_schema,
    build_samples_table_schema,
    build_silac_feature_table_schema,
    build_tmt_channel_map_schema,
    build_transition_table_schema,
    require_valid_scientific_table,
    validate_scientific_table,
)
from bijux_proteomics.identification.contracts import SearchResultColumnMapping
from bijux_proteomics.isotope_labeling.silac_quantification import SilacColumnMapping
from bijux_proteomics.ptm.contracts import PtmLocalizationColumnMapping


def test_validate_scientific_table_reports_missing_column_and_wrong_type(
    tmp_path: Path,
) -> None:
    psm_path = tmp_path / "psms.tsv"
    psm_path.write_text(
        "\n".join(
            (
                "scan\tsequence\tcharge\tscore\tqval",
                "scan_001\tPEPTIDE\t2\t10.5\t0.02",
                "scan_002\tPEPTIDE\twrong\t11.5\t0.03",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_scientific_table(
        psm_path,
        schema=build_psm_table_schema(
            SearchResultColumnMapping(
                spectrum_id="scan",
                peptide="sequence",
                charge="charge",
                score="score",
                q_value="qval",
            )
        ),
    )

    assert len(report.accepted_rows) == 1
    issue_codes = [
        issue.code
        for rejected_row in report.rejected_rows
        for issue in rejected_row.issues
    ]
    assert "wrong_type" in issue_codes

    missing_column_path = tmp_path / "missing.tsv"
    missing_column_path.write_text(
        "scan\tsequence\tcharge\nscan_001\tPEPTIDE\t2\n",
        encoding="utf-8",
    )
    missing_report = validate_scientific_table(
        missing_column_path,
        schema=build_psm_table_schema(
            SearchResultColumnMapping(
                spectrum_id="scan",
                peptide="sequence",
                charge="charge",
                score="score",
            )
        ),
    )

    assert missing_report.rejected_rows[0].issues[0].code == "missing_column"


def test_validate_scientific_table_reports_invalid_q_values_and_negative_intensities(
    tmp_path: Path,
) -> None:
    diann_path = tmp_path / "diann.tsv"
    diann_path.write_text(
        "\n".join(
            (
                "Precursor.Id\tStripped.Sequence\tModified.Sequence\tPrecursor.Charge\tQ.Value\tProtein.Group\tProtein.Ids\tRun\tSample\tPrecursor.Quantity\tPG.Quantity",
                "prec_1\tPEPTIDE\tPEPTIDE\t2\t1.2\tPG1\tP1\trun_a\tsample_a\t100\t1000",
                "prec_2\tPEPTIDE\tPEPTIDE\t2\t0.02\tPG2\tP2\trun_b\tsample_b\t-5\t1000",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_scientific_table(diann_path, schema=build_diann_report_schema())

    issue_codes = [
        issue.code
        for rejected_row in report.rejected_rows
        for issue in rejected_row.issues
    ]
    assert issue_codes.count("invalid_q_value") == 1
    assert issue_codes.count("negative_intensity") == 1


def test_validate_scientific_table_reports_impossible_contrasts_with_context(
    tmp_path: Path,
) -> None:
    contrast_path = tmp_path / "contrasts.tsv"
    contrast_path.write_text(
        "\n".join(
            (
                "contrast_id\tleft_condition\tright_condition\tkind\tpair_id_field",
                "same_vs_same\tcase\tcase\tpairwise\t",
                "missing_vs_ctrl\tmissing\tctrl\tpairwise\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_scientific_table(
        contrast_path,
        schema=build_contrast_table_schema(),
        context=ScientificTableValidationContext(
            known_conditions=("case", "ctrl"),
        ),
    )

    issue_messages = [
        issue.message
        for rejected_row in report.rejected_rows
        for issue in rejected_row.issues
        if issue.code == "impossible_contrast"
    ]
    assert "contrast must compare two distinct conditions" in issue_messages
    assert "contrast references unknown condition 'missing'" in issue_messages


def test_validate_scientific_table_reports_invalid_labels_and_duplicate_channels(
    tmp_path: Path,
) -> None:
    silac_path = tmp_path / "silac.tsv"
    silac_path.write_text(
        "\n".join(
            (
                "feature_id\tsample_id\tpeptide\tprotein_refs\tcharge\tlabel\tintensity",
                "f1\ts1\tPEPTIDE\tP1\t2\tsuperheavy\t10",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    silac_report = validate_scientific_table(
        silac_path,
        schema=build_silac_feature_table_schema(SilacColumnMapping()),
    )

    assert silac_report.rejected_rows[0].issues[0].code == "invalid_label"

    tmt_path = tmp_path / "tmt_map.tsv"
    tmt_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tmultiplex_group\tmultiplex_channel\tsample_role",
                "s1\tcase\t1\t1\trun1\tplex-a\t126\tsample",
                "s2\tctrl\t1\t1\trun2\tplex-a\t126\tsample",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    tmt_report = validate_scientific_table(
        tmt_path,
        schema=build_tmt_channel_map_schema(),
    )

    duplicate_codes = [
        issue.code
        for rejected_row in tmt_report.rejected_rows
        for issue in rejected_row.issues
    ]
    assert "duplicate_identifier" in duplicate_codes


def test_validate_scientific_table_reports_dynamic_maxquant_lfq_intensity_failures(
    tmp_path: Path,
) -> None:
    protein_groups_path = tmp_path / "proteinGroups.txt"
    protein_groups_path.write_text(
        "\n".join(
            (
                "Protein IDs\tMajority protein IDs\tPeptides\tRazor + unique peptides\tMS/MS count\tSequence coverage [%]\tLFQ intensity raw_A\tLFQ intensity raw_B",
                "P1\tP1\t3\t2\t5\t42.0\t1000\t-1",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_scientific_table(
        protein_groups_path,
        schema=build_maxquant_protein_groups_schema(),
    )

    assert report.rejected_rows[0].issues[0].code == "negative_intensity"


def test_require_valid_scientific_table_raises_structured_error(tmp_path: Path) -> None:
    path = tmp_path / "design.tsv"
    path.write_text(
        "sample_id\tcondition\treplicate\tfraction\tspectra_file\n",
        encoding="utf-8",
    )

    with pytest.raises(ScientificTableValidationError) as excinfo:
        require_valid_scientific_table(path, schema=build_experimental_design_schema())

    assert excinfo.value.report.table_kind == "experimental_design"


def test_validate_scientific_table_accepts_minimal_samples_table(
    tmp_path: Path,
) -> None:
    path = tmp_path / "samples.tsv"
    path.write_text(
        "\n".join(
            (
                "sample_id\trun_id\tcondition\tbatch\tpair_id\ttimepoint\tplex_id\tchannel",
                "sample-1\trun-1\tcontrol\tbatch-a\tpair-1\tt0\tplex-a\t126",
                "sample-2\trun-1\ttreated\tbatch-a\tpair-1\tt1\tplex-a\t127N",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = require_valid_scientific_table(path, schema=build_samples_table_schema())

    assert report.table_kind == "sample_metadata"
    assert len(report.accepted_rows) == 2


def test_scientific_table_schemas_cover_real_scientific_table_families() -> None:
    assert build_diann_report_schema().table_kind == "diann_report"
    assert build_maxquant_peptides_schema().table_kind == "maxquant_peptides"
    assert (
        build_maxquant_protein_groups_schema().table_kind == "maxquant_protein_groups"
    )
    assert (
        build_ptm_evidence_schema(
            PtmLocalizationColumnMapping(
                spectrum_id="spectrum_id",
                peptide="peptide",
                charge="charge",
                score="score",
                protein_refs="proteins",
                localization_score="localization_score",
            )
        ).table_kind
        == "ptm_evidence"
    )
    assert build_transition_table_schema().table_kind == "transition_table"
