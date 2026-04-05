from __future__ import annotations

from agentic_proteins.core.failures import FailureType, suggest_next_action


def test_suggest_next_action_maps_failures() -> None:
    assert suggest_next_action(FailureType.NONE) == "none"
    assert suggest_next_action(FailureType.INPUT_INVALID) == "fix_input_sequence"
    assert suggest_next_action(FailureType.TOOL_TIMEOUT) == "retry_with_different_tool"
    assert suggest_next_action(FailureType.OOM) == "reduce_model_size_or_batch"
    assert suggest_next_action(FailureType.BIO_IMPLAUSIBLE) == "review_sequence_constraints"
    assert suggest_next_action(FailureType.HUMAN_DECISION_MISSING) == "provide_signed_human_decision"
