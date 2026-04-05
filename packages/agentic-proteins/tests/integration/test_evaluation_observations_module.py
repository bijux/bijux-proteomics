# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import agentic_proteins.execution.evaluation.observations as obs


def test_observations_module_exports() -> None:
    assert "EvaluationInput" in obs.__all__
    assert hasattr(obs, "Observation")
