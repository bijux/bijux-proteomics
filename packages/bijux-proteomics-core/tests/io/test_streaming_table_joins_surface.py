# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.tables import (
    DelimitedLookupJoinSpec,
    iter_delimited_rows,
    iter_streaming_lookup_join,
)


def test_streaming_lookup_join_matches_in_memory_subset_across_psm_peptide_protein_metadata_and_annotation_tables(
    tmp_path: Path,
) -> None:
    paths = _write_join_subset(tmp_path)
    lookup_specs = (
        DelimitedLookupJoinSpec(
            join_name="peptides",
            path=paths["peptides"],
            primary_key_columns=("peptide_id",),
            lookup_key_columns=("peptide_id",),
            required_lookup_columns=("peptide_sequence",),
        ),
        DelimitedLookupJoinSpec(
            join_name="proteins",
            path=paths["proteins"],
            primary_key_columns=("protein_group_id",),
            lookup_key_columns=("protein_group_id",),
            required_lookup_columns=("representative_protein_ref",),
        ),
        DelimitedLookupJoinSpec(
            join_name="metadata",
            path=paths["metadata"],
            primary_key_columns=("sample_id",),
            lookup_key_columns=("sample_id",),
            required_lookup_columns=("condition",),
        ),
        DelimitedLookupJoinSpec(
            join_name="annotations",
            path=paths["annotations"],
            primary_key_columns=("annotation_id",),
            lookup_key_columns=("annotation_id",),
            required_lookup_columns=("annotation_label",),
        ),
    )

    streamed = tuple(
        {
            "psm_id": joined.primary_row["psm_id"],
            "peptide_sequence": joined.joined_rows["peptides"][0]["peptide_sequence"],
            "protein_ref": joined.joined_rows["proteins"][0][
                "representative_protein_ref"
            ],
            "condition": joined.joined_rows["metadata"][0]["condition"],
            "annotation_label": joined.joined_rows["annotations"][0][
                "annotation_label"
            ],
        }
        for joined in iter_streaming_lookup_join(
            paths["psms"],
            lookup_specs=lookup_specs,
            required_primary_columns=(
                "psm_id",
                "peptide_id",
                "protein_group_id",
                "sample_id",
                "annotation_id",
            ),
        )
    )

    in_memory = _build_in_memory_join(paths)

    assert streamed == in_memory


def test_iter_delimited_rows_reports_missing_required_columns(tmp_path: Path) -> None:
    path = tmp_path / "psms.tsv"
    path.write_text("psm_id\tpeptide_id\npsm-1\tpep-1\n", encoding="utf-8")

    try:
        tuple(
            iter_delimited_rows(
                path,
                required_columns=("psm_id", "protein_group_id"),
            )
        )
    except ValueError as exc:
        assert "missing required columns" in str(exc)
        assert "protein_group_id" in str(exc)
    else:
        raise AssertionError("missing required columns should raise ValueError")


def _build_in_memory_join(paths: dict[str, Path]) -> tuple[dict[str, str], ...]:
    peptides = {
        row["peptide_id"]: row for _, row in iter_delimited_rows(paths["peptides"])
    }
    proteins = {
        row["protein_group_id"]: row
        for _, row in iter_delimited_rows(paths["proteins"])
    }
    metadata = {
        row["sample_id"]: row for _, row in iter_delimited_rows(paths["metadata"])
    }
    annotations = {
        row["annotation_id"]: row
        for _, row in iter_delimited_rows(paths["annotations"])
    }
    return tuple(
        {
            "psm_id": row["psm_id"],
            "peptide_sequence": peptides[row["peptide_id"]]["peptide_sequence"],
            "protein_ref": proteins[row["protein_group_id"]][
                "representative_protein_ref"
            ],
            "condition": metadata[row["sample_id"]]["condition"],
            "annotation_label": annotations[row["annotation_id"]]["annotation_label"],
        }
        for _, row in iter_delimited_rows(paths["psms"])
    )


def _write_join_subset(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "psms": tmp_path / "psms.tsv",
        "peptides": tmp_path / "peptides.tsv",
        "proteins": tmp_path / "proteins.tsv",
        "metadata": tmp_path / "metadata.tsv",
        "annotations": tmp_path / "annotations.tsv",
    }
    paths["psms"].write_text(
        "\n".join(
            (
                "psm_id\tpeptide_id\tprotein_group_id\tsample_id\tannotation_id",
                "psm-1\tpep-1\tpg-1\tsample-a\tann-kinase",
                "psm-2\tpep-2\tpg-2\tsample-b\tann-membrane",
                "psm-3\tpep-3\tpg-1\tsample-a\tann-kinase",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    paths["peptides"].write_text(
        "\n".join(
            (
                "peptide_id\tpeptide_sequence",
                "pep-1\tPEPTIDER",
                "pep-2\tAAAAK",
                "pep-3\tMKWVTFISL",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    paths["proteins"].write_text(
        "\n".join(
            (
                "protein_group_id\trepresentative_protein_ref",
                "pg-1\tP11111",
                "pg-2\tP22222",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    paths["metadata"].write_text(
        "\n".join(
            (
                "sample_id\tcondition",
                "sample-a\tcontrol",
                "sample-b\ttreated",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    paths["annotations"].write_text(
        "\n".join(
            (
                "annotation_id\tannotation_label",
                "ann-kinase\tpathway:kinase",
                "ann-membrane\tcontext:membrane",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return paths
