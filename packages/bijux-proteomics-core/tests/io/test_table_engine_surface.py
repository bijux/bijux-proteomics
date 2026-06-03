# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import string
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from bijux_proteomics._tabular import (
    DelimitedColumnSpec,
    DelimitedColumnValueType,
    infer_delimited_table_delimiter,
    parse_delimited_table,
    render_rows_tsv,
    render_tsv_rows,
)
from bijux_proteomics_foundation.testing.skip_policy import (
    import_hypothesis_or_skip,
)

if TYPE_CHECKING:
    from hypothesis import given, settings
    from hypothesis import strategies as st
else:
    hypothesis = import_hypothesis_or_skip(
        reason="hypothesis is required for the delimited table property-based surface",
    )
    given = hypothesis.given
    settings = hypothesis.settings
    st = hypothesis.strategies

_SAFE_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "-_./",
    min_size=1,
    max_size=12,
).filter(
    lambda value: value.strip().lower() not in {"", "na", "n/a", "null", "none", "nan"}
)
_OPTIONAL_TEXT = st.one_of(st.none(), _SAFE_TEXT)
_SMALL_FLOAT = st.one_of(
    st.none(),
    st.integers(min_value=-10_000, max_value=10_000).map(lambda value: value / 10.0),
)
_TABLE_ROW = st.fixed_dictionaries(
    {
        "sample_id": _SAFE_TEXT,
        "replicate": st.integers(min_value=1, max_value=12),
        "intensity": _SMALL_FLOAT,
        "contaminant": st.one_of(st.none(), st.booleans()),
        "note": _OPTIONAL_TEXT,
        "extra_info": _OPTIONAL_TEXT,
    }
)
_REPLICATE_TOKEN = st.one_of(
    st.integers(min_value=1, max_value=12).map(str),
    st.sampled_from(("", "NA", "one", "1.5", "false")),
)
_INTENSITY_TOKEN = st.one_of(
    st.integers(min_value=-10_000, max_value=10_000).map(
        lambda value: f"{value / 10:g}"
    ),
    st.sampled_from(("", "NA", "abc", "true")),
)
_BOOLEAN_TOKEN = st.one_of(
    st.sampled_from(("true", "false", "1", "0", "yes", "no", "", "NA", "maybe", "2")),
)
_RAW_TABLE_ROW = st.fixed_dictionaries(
    {
        "sample_id": _SAFE_TEXT,
        "replicate": _REPLICATE_TOKEN,
        "intensity": _INTENSITY_TOKEN,
        "contaminant": _BOOLEAN_TOKEN,
    }
)


def _expected_generated_row_issue_codes(row: dict[str, str]) -> tuple[str, ...]:
    issue_codes: list[str] = []
    replicate_value = row["replicate"].strip().lower()
    if replicate_value in {"", "na", "n/a", "null", "none", "nan"}:
        issue_codes.append("missing_required_value")
    else:
        try:
            int(row["replicate"].strip())
        except ValueError:
            issue_codes.append("invalid_integer_value")

    intensity_value = row["intensity"].strip().lower()
    if intensity_value not in {"", "na", "n/a", "null", "none", "nan"}:
        try:
            float(row["intensity"].strip())
        except ValueError:
            issue_codes.append("invalid_float_value")

    contaminant_value = row["contaminant"].strip().lower()
    if contaminant_value not in {
        "",
        "na",
        "n/a",
        "null",
        "none",
        "nan",
    } and contaminant_value not in {
        "true",
        "false",
        "1",
        "0",
        "yes",
        "no",
        "y",
        "n",
    }:
        issue_codes.append("invalid_boolean_value")
    return tuple(issue_codes)


def test_parse_delimited_table_supports_required_columns_coercion_and_missing_values(
    tmp_path: Path,
) -> None:
    table_path = tmp_path / "quant.csv"
    table_path.write_text(
        "sample_id,replicate,intensity,contaminant\ns1,1,12.5,false\ns2,2,NA,true\n",
        encoding="utf-8",
    )

    report = parse_delimited_table(
        table_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(
                name="replicate",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="intensity",
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="contaminant",
                value_type=DelimitedColumnValueType.BOOLEAN,
            ),
        ),
    )

    assert report.delimiter == ","
    assert report.rejected_rows == ()
    assert len(report.accepted_rows) == 2
    assert report.accepted_rows[0].values["replicate"] == 1
    assert report.accepted_rows[0].values["intensity"] == 12.5
    assert report.accepted_rows[1].values["intensity"] is None
    assert report.accepted_rows[1].values["contaminant"] is True


def test_parse_delimited_table_reports_header_and_row_failures(tmp_path: Path) -> None:
    missing_header_path = tmp_path / "missing.tsv"
    missing_header_path.write_text("sample_id\tintensity\ns1\t10\n", encoding="utf-8")

    header_report = parse_delimited_table(
        missing_header_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(name="replicate", required=True),
        ),
    )

    assert len(header_report.rejected_rows) == 1
    assert header_report.rejected_rows[0].issues[0].code == "missing_required_column"

    invalid_row_path = tmp_path / "invalid.tsv"
    invalid_row_path.write_text(
        "sample_id\treplicate\ns1\tone\n",
        encoding="utf-8",
    )

    row_report = parse_delimited_table(
        invalid_row_path,
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(
                name="replicate",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
        ),
    )

    assert row_report.accepted_rows == ()
    assert len(row_report.rejected_rows) == 1
    assert row_report.rejected_rows[0].row_number == 2
    assert row_report.rejected_rows[0].issues[0].code == "invalid_integer_value"


def test_table_engine_infers_delimiter_and_renders_stable_tsv() -> None:
    assert infer_delimited_table_delimiter("a\tb") == "\t"
    assert infer_delimited_table_delimiter("a,b") == ","

    rendered = render_rows_tsv(
        fieldnames=("sample_id", "replicate", "intensity", "accepted"),
        rows=(
            {
                "sample_id": "s1",
                "replicate": 1,
                "intensity": 12.5,
                "accepted": True,
            },
            {
                "sample_id": "s2",
                "replicate": 2,
                "intensity": None,
                "accepted": False,
            },
        ),
    )

    assert rendered == (
        "sample_id\treplicate\tintensity\taccepted\ns1\t1\t12.5\ttrue\ns2\t2\t\tfalse\n"
    )
    assert (
        render_tsv_rows(
            fieldnames=("sample_id", "replicate", "intensity", "accepted"),
            rows=(
                {
                    "sample_id": "s1",
                    "replicate": 1,
                    "intensity": 12.5,
                    "accepted": True,
                },
                {
                    "sample_id": "s2",
                    "replicate": 2,
                    "intensity": None,
                    "accepted": False,
                },
            ),
        )
        == rendered
    )


@given(rows=st.lists(_TABLE_ROW, min_size=1, max_size=5))
@settings(deadline=None, max_examples=30)
def test_parse_delimited_table_round_trips_generated_valid_rows(
    rows: list[dict[str, str | int | float | bool | None]],
) -> None:
    with TemporaryDirectory() as temp_dir:
        table_path = Path(temp_dir) / "generated_quant.tsv"
        table_path.write_text(
            render_rows_tsv(
                fieldnames=(
                    "sample_id",
                    "replicate",
                    "intensity",
                    "contaminant",
                    "note",
                    "extra_info",
                ),
                rows=tuple(rows),
            ),
            encoding="utf-8",
        )

        report = parse_delimited_table(
            table_path,
            column_specs=(
                DelimitedColumnSpec(name="sample_id", required=True),
                DelimitedColumnSpec(
                    name="replicate",
                    required=True,
                    value_type=DelimitedColumnValueType.INTEGER,
                ),
                DelimitedColumnSpec(
                    name="intensity",
                    value_type=DelimitedColumnValueType.FLOAT,
                ),
                DelimitedColumnSpec(
                    name="contaminant",
                    value_type=DelimitedColumnValueType.BOOLEAN,
                ),
                DelimitedColumnSpec(name="note"),
            ),
        )

        assert report.delimiter == "\t"
        assert report.rejected_rows == ()
        assert len(report.accepted_rows) == len(rows)
        assert tuple(row.row_number for row in report.accepted_rows) == tuple(
            range(2, len(rows) + 2)
        )
        assert tuple(row.values for row in report.accepted_rows) == tuple(
            {
                "sample_id": row["sample_id"],
                "replicate": row["replicate"],
                "intensity": row["intensity"],
                "contaminant": row["contaminant"],
                "note": row["note"],
            }
            for row in rows
        )
        assert tuple(row.extra_values for row in report.accepted_rows) == tuple(
            {} if row["extra_info"] is None else {"extra_info": row["extra_info"]}
            for row in rows
        )


@given(rows=st.lists(_RAW_TABLE_ROW, min_size=1, max_size=5))
@settings(deadline=None, max_examples=30)
def test_parse_delimited_table_preserves_generated_rejection_invariants(
    rows: list[dict[str, str]],
) -> None:
    with TemporaryDirectory() as temp_dir:
        table_path = Path(temp_dir) / "generated_invalid_quant.tsv"
        table_path.write_text(
            render_rows_tsv(
                fieldnames=("sample_id", "replicate", "intensity", "contaminant"),
                rows=tuple(rows),
            ),
            encoding="utf-8",
        )

        report = parse_delimited_table(
            table_path,
            column_specs=(
                DelimitedColumnSpec(name="sample_id", required=True),
                DelimitedColumnSpec(
                    name="replicate",
                    required=True,
                    value_type=DelimitedColumnValueType.INTEGER,
                ),
                DelimitedColumnSpec(
                    name="intensity",
                    value_type=DelimitedColumnValueType.FLOAT,
                ),
                DelimitedColumnSpec(
                    name="contaminant",
                    value_type=DelimitedColumnValueType.BOOLEAN,
                ),
            ),
        )

        expected_issue_codes = tuple(
            _expected_generated_row_issue_codes(row) for row in rows
        )
        assert report.header == ("sample_id", "replicate", "intensity", "contaminant")
        assert len(report.accepted_rows) + len(report.rejected_rows) == len(rows)
        all_rows = report.accepted_rows + report.rejected_rows
        assert tuple(sorted(row.row_number for row in all_rows)) == tuple(
            range(2, len(rows) + 2)
        )
        assert tuple(
            tuple(issue.code for issue in rejected_row.issues)
            for rejected_row in report.rejected_rows
        ) == tuple(issue_codes for issue_codes in expected_issue_codes if issue_codes)
