# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    DiaCapabilityMatrixEntry,
    DiaCapabilityStatus,
    build_dia_capability_matrix,
)


def test_build_dia_capability_matrix_counts_statuses() -> None:
    report = build_dia_capability_matrix(
        (
            DiaCapabilityMatrixEntry(
                surface="import",
                status=DiaCapabilityStatus.SUPPORTED,
                note="DIA-NN import is implemented",
            ),
            DiaCapabilityMatrixEntry(
                surface="library_validation",
                status=DiaCapabilityStatus.SUPPORTED,
                note="identity and validation are available",
            ),
            DiaCapabilityMatrixEntry(
                surface="fdr",
                status=DiaCapabilityStatus.PARTIAL,
                note="group-level safeguards still required",
            ),
            DiaCapabilityMatrixEntry(
                surface="unsupported_engine_x",
                status=DiaCapabilityStatus.UNSUPPORTED,
                note="no adapter coverage",
            ),
        )
    )

    assert report.supported_count == 2
    assert report.partial_count == 1
    assert report.unsupported_count == 1
