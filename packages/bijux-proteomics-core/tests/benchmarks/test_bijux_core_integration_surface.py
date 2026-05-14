# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.adoption import (
    BijuxCoreIntegrationContractInput,
    build_bijux_core_integration_contract_report,
)


def test_build_bijux_core_integration_contract_report_flags_incompatibility() -> None:
    report = build_bijux_core_integration_contract_report(
        BijuxCoreIntegrationContractInput(
            contract_id="core-dag-v1",
            dag_nodes_emitted=("protein", "candidate"),
            edge_types_emitted=("supports",),
            evidence_payload_refs=("evidence://claim/44",),
            incompatible_surfaces=("missing-core-edge-metadata",),
        )
    )

    assert report.compatible is False
    assert report.incompatible_surfaces == ("missing-core-edge-metadata",)
