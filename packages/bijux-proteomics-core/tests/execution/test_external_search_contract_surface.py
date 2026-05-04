# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.execution.providers import (
    build_external_search_execution_contract,
)


def test_build_external_search_execution_contract_tracks_command_context() -> None:
    contract = build_external_search_execution_contract(
        command=("sage", "--config", "config.toml"),
        input_paths=("inputs/db.fasta", "inputs/run.mzml"),
        output_paths=("outputs/search.psms.tsv",),
        params={"enzyme": "trypsin", "precursor_tolerance": "20ppm"},
        env={"OMP_NUM_THREADS": "8"},
        container_image="ghcr.io/bijux/sage-runtime",
        tool_version="0.14.7",
        failure_modes=("missing_fasta", "empty_psm_output"),
    )

    assert contract.command[0] == "sage"
    assert contract.params["enzyme"] == "trypsin"
    assert contract.failure_modes[0] == "empty_psm_output"
