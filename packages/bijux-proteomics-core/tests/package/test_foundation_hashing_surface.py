# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab.qc import _stable_sha256
from bijux_proteomics.study.qc import QcPublicationDecision
from bijux_proteomics_foundation import hash_model


def test_core_qc_hashing_reuses_foundation_model_hashing() -> None:
    decision = QcPublicationDecision(
        run_id="run-77",
        publish_allowed=False,
        promote_allowed=False,
        blocking_metric_keys=("contaminant_fraction",),
        reason="qc gate blocked publication",
        advisory_metric_keys=("retention_time_spread",),
    )

    assert _stable_sha256(decision) == hash_model(decision)
