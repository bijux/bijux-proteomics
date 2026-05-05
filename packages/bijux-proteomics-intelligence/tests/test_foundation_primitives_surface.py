# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pydantic import ValidationError
import pytest

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.briefs import DesignBrief


def test_intelligence_briefs_use_foundation_model_and_identifier_primitives() -> None:
    brief = DesignBrief(
        program_id="prog-intelligence",
        target_id="target-intelligence",
        objective="Rank candidates honestly",
        mechanism="allosteric modulation",
    )

    assert issubclass(DesignBrief, JsonModel)
    assert brief.program_id == "prog-intelligence"

    with pytest.raises(ValidationError):
        DesignBrief(
            program_id="Program Intelligence",
            target_id="target-intelligence",
            objective="Rank candidates honestly",
            mechanism="allosteric modulation",
        )
