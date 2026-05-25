# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from pathlib import Path
import string
from tempfile import TemporaryDirectory

from bijux_proteomics.io.formats import (
    ExperimentalDesignSampleRole,
    parse_experimental_design_table,
)
from bijux_proteomics_foundation.testing.skip_policy import (
    SkipCategory,
    import_or_skip,
)

hypothesis = import_or_skip(
    "hypothesis",
    category=SkipCategory.OPTIONAL_DEPENDENCY,
    reason="hypothesis is required for the experimental design property-based surface",
)
given = hypothesis.given
settings = hypothesis.settings
st = hypothesis.strategies

_SAFE_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "-_./",
    min_size=1,
    max_size=12,
).filter(
    lambda value: value.strip().lower()
    not in {"", "na", "n/a", "null", "none", "nan"}
)
_OPTIONAL_TEXT = st.one_of(st.none(), _SAFE_TEXT)
_DESIGN_ROW = st.fixed_dictionaries(
    {
        "sample_id": _SAFE_TEXT,
        "condition": _SAFE_TEXT,
        "replicate": st.integers(min_value=1, max_value=4),
        "fraction": st.integers(min_value=1, max_value=3),
        "spectra_file": _SAFE_TEXT.map(lambda value: f"{value}.mzML"),
        "cohort": _OPTIONAL_TEXT,
        "batch": _OPTIONAL_TEXT,
        "pair_id": _OPTIONAL_TEXT,
        "technical_replicate_id": _OPTIONAL_TEXT,
        "run_order": st.one_of(st.none(), st.integers(min_value=1, max_value=12)),
        "panel": _OPTIONAL_TEXT,
    }
)


def test_parse_experimental_design_table_accepts_csv_rows_and_metadata(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "study_design.csv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id,condition,replicate,fraction,spectra_file,batch,panel",
                "s1,treated,1,1,run_a.mzML,b1,cohort-a",
                "s2,control,2,1,run_b.mzML,b1,cohort-a",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 2
    assert report.accepted_entries[0].replicate == 1
    assert report.accepted_entries[0].fraction == 1
    assert report.accepted_entries[0].sample_role is ExperimentalDesignSampleRole.SAMPLE
    assert report.accepted_entries[0].metadata["panel"] == "cohort-a"


def test_parse_experimental_design_table_rejects_missing_required_columns(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "missing_design.tsv"
    design_path.write_text(
        "sample_id\tcondition\treplicate\tfraction\ns1\ttreated\t1\t1\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 1
    assert report.rejected_rows[0].row_number == 1
    assert report.rejected_rows[0].issues[0].code == "missing_design_column"
    assert report.rejected_rows[0].issues[0].field == "spectra_file"


def test_parse_experimental_design_table_preserves_row_validation_semantics(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "invalid_design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tsample_role",
                "s1\ttreated\tone\t1\trun_a.mzML\tsample",
                "s2\tcontrol\t2\t1\trun_b.mzML\tqc_bridge",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.accepted_entries == ()
    assert len(report.rejected_rows) == 2
    assert report.rejected_rows[0].issues[0].code == "invalid_design_row"
    assert "invalid integer value" in report.rejected_rows[0].issues[0].message
    assert report.rejected_rows[1].issues[0].code == "invalid_design_row"
    assert "non-sample multiplex roles require explicit multiplex_group" in (
        report.rejected_rows[1].issues[0].message
    )


def test_parse_experimental_design_table_accepts_multi_run_sample_rows(
    tmp_path: Path,
) -> None:
    design_path = tmp_path / "duplicate_design.tsv"
    design_path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\ttechnical_replicate_id",
                "s1\ttreated\t1\t1\trun_a.mzML\ttech-1",
                "s1\ttreated\t1\t1\trun_b.mzML\ttech-2",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_experimental_design_table(design_path)

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 2
    assert report.accepted_entries[0].sample_id == "s1"
    assert report.accepted_entries[0].technical_replicate_id == "tech-1"
    assert report.accepted_entries[1].technical_replicate_id == "tech-2"


def test_parse_experimental_design_table_accepts_explicit_run_order() -> None:
    design_path = Path(__file__).resolve().parent.parent / "fixtures" / "formats" / "skyline_targeted_carryover.design.tsv"

    report = parse_experimental_design_table(design_path)

    assert report.rejected_rows == ()
    assert len(report.accepted_entries) == 4
    assert report.accepted_entries[0].run_order == 1
    assert report.accepted_entries[1].run_order == 2
    assert report.accepted_entries[-1].run_order == 4


@given(
    delimiter=st.sampled_from((",", "\t")),
    rows=st.lists(
        _DESIGN_ROW,
        min_size=1,
        max_size=5,
        unique_by=lambda row: (row["sample_id"], row["spectra_file"]),
    ),
)
@settings(deadline=None, max_examples=30)
def test_parse_experimental_design_table_round_trips_generated_valid_rows(
    delimiter: str,
    rows: list[dict[str, str | int | None]],
) -> None:
    with TemporaryDirectory() as temp_dir:
        design_path = Path(temp_dir) / (
            "generated_design.csv" if delimiter == "," else "generated_design.tsv"
        )
        with design_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter=delimiter, lineterminator="\n")
            writer.writerow(
                (
                    "sample_id",
                    "condition",
                    "replicate",
                    "fraction",
                    "spectra_file",
                    "cohort",
                    "batch",
                    "pair_id",
                    "technical_replicate_id",
                    "run_order",
                    "panel",
                )
            )
            for row in rows:
                writer.writerow(
                    (
                        row["sample_id"],
                        row["condition"],
                        row["replicate"],
                        row["fraction"],
                        row["spectra_file"],
                        row["cohort"],
                        row["batch"],
                        row["pair_id"],
                        row["technical_replicate_id"],
                        row["run_order"],
                        row["panel"],
                    )
                )

        report = parse_experimental_design_table(design_path)

        assert report.rejected_rows == ()
        assert len(report.accepted_entries) == len(rows)
        assert tuple(entry.sample_role for entry in report.accepted_entries) == tuple(
            ExperimentalDesignSampleRole.SAMPLE for _ in rows
        )
        assert tuple(entry.sample_id for entry in report.accepted_entries) == tuple(
            str(row["sample_id"]) for row in rows
        )
        assert tuple(entry.condition for entry in report.accepted_entries) == tuple(
            str(row["condition"]) for row in rows
        )
        assert tuple(entry.run_order for entry in report.accepted_entries) == tuple(
            row["run_order"] for row in rows
        )
        assert tuple(entry.metadata for entry in report.accepted_entries) == tuple(
            {} if row["panel"] is None else {"panel": str(row["panel"])} for row in rows
        )
