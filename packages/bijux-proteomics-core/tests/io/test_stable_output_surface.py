# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass

from bijux_proteomics.io.stable_outputs import (
    sort_rows_by_fields,
    sort_strings,
    stable_json_dumps,
)


@dataclass(frozen=True)
class _Row:
    sample_id: str
    entity_id: str
    score: float


def test_stable_json_dumps_sorts_keys() -> None:
    payload = {"zeta": 1, "alpha": {"gamma": 2, "beta": 3}}

    rendered = stable_json_dumps(payload, indent=2)

    assert (
        rendered
        == '{\n  "alpha": {\n    "beta": 3,\n    "gamma": 2\n  },\n  "zeta": 1\n}'
    )


def test_sort_rows_by_fields_orders_rows_deterministically() -> None:
    rows = (
        _Row(sample_id="sample_b", entity_id="P2", score=2.0),
        _Row(sample_id="sample_a", entity_id="P2", score=3.0),
        _Row(sample_id="sample_a", entity_id="P1", score=1.0),
    )

    ordered = sort_rows_by_fields(rows, "entity_id", "sample_id")

    assert ordered == (
        _Row(sample_id="sample_a", entity_id="P1", score=1.0),
        _Row(sample_id="sample_a", entity_id="P2", score=3.0),
        _Row(sample_id="sample_b", entity_id="P2", score=2.0),
    )


def test_sort_strings_returns_canonical_order() -> None:
    assert sort_strings(("sample_b", "sample_a", "sample_c")) == (
        "sample_a",
        "sample_b",
        "sample_c",
    )
