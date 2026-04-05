from __future__ import annotations

from agentic_proteins.core.costs import CostSummary
from agentic_proteins.core.determinism import stable_sort
from agentic_proteins.core.identifiers import deterministic_id


def test_cost_summary_accumulates_and_reads() -> None:
    summary = CostSummary()
    summary.add("cpu", 1.5)
    summary.add("cpu", 0.5)
    assert summary.get("cpu") == 2.0
    assert summary.get("missing") == 0.0


def test_stable_sort_orders_strings() -> None:
    assert stable_sort(["b", "a", "c"]) == ["a", "b", "c"]


def test_deterministic_id_is_stable() -> None:
    payload = {"b": 2, "a": 1}
    assert deterministic_id("run", payload) == deterministic_id("run", payload)
