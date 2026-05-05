# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.review import (
    ContradictionObservation,
    classify_contradictions,
)


def test_classify_contradictions_assigns_deterministic_categories() -> None:
    fixture = json.loads(
        (
            Path(__file__).resolve().parent.parent
            / "fixtures"
            / "review"
            / "contradiction_taxonomy_cases.json"
        ).read_text(encoding="utf-8")
    )
    report = classify_contradictions(
        tuple(
            ContradictionObservation.model_validate(item)
            for item in fixture["observations"]
        )
    )

    categories = {entry.contradiction_id: entry.category for entry in report.entries}
    assert categories["cx-1"] == "source_disagreement"
    assert categories["cx-2"] == "method_disagreement"
    assert categories["cx-3"] == "quant_disagreement"
    assert report.category_counts["source_disagreement"] == 1
    assert report.category_counts["method_disagreement"] == 1
    assert report.category_counts["quant_disagreement"] == 1
