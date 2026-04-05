# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.agents.analysis.failure_analysis import FailureAnalysisAgent
from agentic_proteins.agents.schemas import (
    FailureAnalysisAgentInput,
    InputValidationAgentInput,
)
from agentic_proteins.agents.verification.input_validation import InputValidationAgent
from agentic_proteins.core.failures import FailureType


def test_input_validation_agent_accepts_valid_sequence() -> None:
    agent = InputValidationAgent()
    payload = InputValidationAgentInput(sequence="ACDE", sequence_id="seq-1")
    result = agent.decide(payload)
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_input_validation_agent_flags_invalid_residues() -> None:
    agent = InputValidationAgent()
    payload = InputValidationAgentInput(sequence="AXZ", sequence_id="seq-2")
    result = agent.decide(payload)
    assert result.valid is False
    assert "invalid_residues" in result.errors
    assert "invalid:X,Z" in result.warnings


def test_input_validation_agent_flags_empty_after_strip() -> None:
    agent = InputValidationAgent()
    payload = InputValidationAgentInput(sequence=" ", sequence_id="seq-3")
    result = agent.decide(payload)
    assert result.valid is False
    assert "empty_sequence" in result.errors


def test_failure_analysis_agent_reports_failure_metadata() -> None:
    agent = FailureAnalysisAgent()
    payload = FailureAnalysisAgentInput(
        tool_name="tool",
        status="failed",
        error_type="timeout",
        error_message="boom",
    )
    result = agent.decide(payload)
    assert result.failure_type == FailureType.TOOL_FAILURE.value
    assert "error_type:timeout" in result.metadata
    assert "has_error_message" in result.metadata
    assert result.replan_recommended is True


def test_failure_analysis_agent_reports_success() -> None:
    agent = FailureAnalysisAgent()
    payload = FailureAnalysisAgentInput(
        tool_name="tool",
        status="success",
        error_type="none",
        error_message="none",
    )
    result = agent.decide(payload)
    assert result.failure_type == FailureType.UNKNOWN.value
    assert result.metadata == []
    assert result.replan_recommended is False
