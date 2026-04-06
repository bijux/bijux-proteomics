# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import ExperimentPlan, fingerprint_model, to_canonical_json


def test_lab_canonical_serialization_and_fingerprint_are_stable() -> None:
    plan = ExperimentPlan(program_id="prog-ser")
    canonical = to_canonical_json(plan)
    digest_a = fingerprint_model(plan)
    digest_b = fingerprint_model(plan)

    assert canonical.startswith("{")
    assert digest_a == digest_b
