# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Failure taxonomy primitives."""

from __future__ import annotations

from enum import Enum


class FailureType(str, Enum):
    """FailureType."""

    NONE = "none"
    INPUT_INVALID = "input_invalid"
    INVALID_PLAN = "invalid_plan"
    CAPABILITY_MISSING = "capability_missing"
    TOOL_TIMEOUT = "tool_timeout"
    OOM = "oom"
    TOOL_CRASH = "tool_crash"
    TOOL_FAILURE = "tool_failure"
    INVALID_OUTPUT = "invalid_output"
    BIO_IMPLAUSIBLE = "biological_implausibility"
    CONVERGENCE_FAILURE = "convergence_failure"
    HUMAN_DECISION_MISSING = "human_decision_missing"
    UNKNOWN = "unknown"


def suggest_next_action(failure_type: FailureType) -> str:
    """suggest_next_action."""
    if failure_type == FailureType.NONE:
        return "none"
    if failure_type == FailureType.INPUT_INVALID:
        return "fix_input_sequence"
    if failure_type == FailureType.INVALID_PLAN:
        return "repair_planning_graph"
    if failure_type == FailureType.CAPABILITY_MISSING:
        return "resolve_provider_requirements"
    if failure_type in {
        FailureType.TOOL_TIMEOUT,
        FailureType.TOOL_CRASH,
        FailureType.TOOL_FAILURE,
    }:
        return "retry_with_different_tool"
    if failure_type == FailureType.OOM:
        return "reduce_model_size_or_batch"
    if failure_type == FailureType.INVALID_OUTPUT:
        return "inspect_tool_outputs"
    if failure_type == FailureType.BIO_IMPLAUSIBLE:
        return "review_sequence_constraints"
    if failure_type == FailureType.CONVERGENCE_FAILURE:
        return "adjust_mutation_plan_or_stop"
    if failure_type == FailureType.HUMAN_DECISION_MISSING:
        return "provide_signed_human_decision"
    return "manual_review"
