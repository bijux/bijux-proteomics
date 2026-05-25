# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    RejectedPsmRow,
    SearchResultValidationIssue,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    build_rejected_evidence_rows_from_psm_rows,
    build_rejected_evidence_rows_from_scientific_rows,
    render_rejected_evidence_tsv,
)
from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
)


def test_rejected_evidence_table_preserves_required_columns_and_reason_codes() -> None:
    rows = build_rejected_evidence_rows_from_psm_rows(
        (
            RejectedPsmRow(
                row_number=4,
                raw_fields={"spectrum_id": "scan-004", "peptide": "PEPTIDE"},
                issues=(
                    SearchResultValidationIssue(
                        code="invalid_charge",
                        message="charge must be an integer",
                        row_number=4,
                    ),
                    SearchResultValidationIssue(
                        code="invalid_q_value",
                        message="q-value must be between 0 and 1",
                        row_number=4,
                    ),
                ),
            ),
        ),
        source_file="generic.tsv",
    )

    assert len(rows) == 2
    assert rows[0].source_file == "generic.tsv"
    assert rows[0].row_number == 4
    assert rows[0].entity_type == "psm"
    assert rows[0].entity_id == "scan-004"
    assert rows[0].reason_code == "invalid_charge"
    assert rows[0].detail == "charge must be an integer"
    assert rows[1].reason_code == "invalid_q_value"

    rendered = render_rejected_evidence_tsv(rows)
    assert rendered.startswith(
        "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
    )
    assert "generic.tsv\t4\tpsm\tscan-004\tinvalid_charge\tcharge must be an integer" in rendered


def test_rejected_evidence_table_builds_precursor_and_feature_rows_from_scientific_rejections() -> (
    None
):
    precursor_rows = build_rejected_evidence_rows_from_scientific_rows(
        (
            ScientificTableRejectedRow(
                row_number=3,
                raw_values={"Precursor.Id": "raw_B_BADQ_2"},
                issues=(
                    ScientificTableValidationIssue(
                        table_kind="diann_report",
                        code="invalid_q_value",
                        message="Q.Value must be between 0 and 1",
                        row_number=3,
                    ),
                ),
            ),
        ),
        source_file="diann_invalid.tsv",
        entity_type="precursor",
    )
    feature_rows = build_rejected_evidence_rows_from_scientific_rows(
        (
            ScientificTableRejectedRow(
                row_number=6,
                raw_values={"FeatureID": "feature-006"},
                issues=(
                    ScientificTableValidationIssue(
                        table_kind="openms_feature_table",
                        code="invalid_intensity",
                        message="intensity must be non-negative",
                        row_number=6,
                    ),
                ),
            ),
        ),
        source_file="openms_features.tsv",
        entity_type="ms1_feature",
    )

    assert precursor_rows[0].entity_id == "raw_B_BADQ_2"
    assert precursor_rows[0].reason_code == "invalid_q_value"
    assert feature_rows[0].entity_id == "feature-006"
    assert feature_rows[0].reason_code == "invalid_intensity"
    assert feature_rows[0].detail == "intensity must be non-negative"
