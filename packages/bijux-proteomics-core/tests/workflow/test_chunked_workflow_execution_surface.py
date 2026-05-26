# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_dda_biological_workflow_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_chunked_biological_report_bundle_matches_non_chunked_bundle() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    eager = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    chunked = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
        chunk_size_rows=2,
    )

    assert chunked.to_stable_json() == eager.to_stable_json()


def test_chunked_generic_dda_bundle_matches_non_chunked_bundle() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    eager = build_dda_biological_workflow_bundle(
        _fixture("dda_biological_results.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.GENERIC,
        generic_mapping_path=_fixture("dda_biological_mapping.json"),
        condition_a="control",
        condition_b="treatment",
    )
    chunked = build_dda_biological_workflow_bundle(
        _fixture("dda_biological_results.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.GENERIC,
        generic_mapping_path=_fixture("dda_biological_mapping.json"),
        condition_a="control",
        condition_b="treatment",
        chunk_size_rows=2,
    )

    assert chunked.to_stable_json() == eager.to_stable_json()
