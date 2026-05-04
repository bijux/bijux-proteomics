# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.execution.providers import (
    build_external_quant_execution_contract,
)


def test_build_external_quant_execution_contract_tracks_artifacts_and_mode() -> None:
    contract = build_external_quant_execution_contract(
        command=("diann", "--matrices"),
        input_paths=("inputs/diann.tsv",),
        output_artifacts=("outputs/precursor.tsv", "outputs/protein.tsv"),
        params={"qvalue": "0.01"},
        env={"OMP_NUM_THREADS": "8"},
        container_image="ghcr.io/bijux/diann-runtime",
        tool_version="1.8.2",
        execution_mode="external_quant",
    )

    assert contract.execution_mode == "external_quant"
    assert contract.output_artifacts[0] == "outputs/precursor.tsv"
