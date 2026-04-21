"""Biology-inspired agentic abstractions."""

from __future__ import annotations

from bijux_proteomics.biology.pathway import ExecutionMode, PathwayContract, PathwayExecutor
from bijux_proteomics.biology.protein_agent import (
    FailureEvent,
    ProteinAgent,
    ProteinConstraints,
    ProteinFailure,
    ProteinLifecycle,
    ProteinState,
)
from bijux_proteomics.biology.regulator import (
    ApprovalMode,
    LLMAction,
    LLMAuthorityBoundary,
    LLMFailureMode,
    LLMObservation,
    LLMRegulator,
    PermissionMode,
    Proposal,
)
from bijux_proteomics.biology.signals import SignalPayload, SignalScope, SignalType
from bijux_proteomics.biology.validation import validate_transition

__all__ = [
    "ExecutionMode",
    "FailureEvent",
    "PathwayContract",
    "PathwayExecutor",
    "LLMRegulator",
    "ApprovalMode",
    "LLMAuthorityBoundary",
    "LLMAction",
    "LLMFailureMode",
    "LLMObservation",
    "PermissionMode",
    "Proposal",
    "ProteinAgent",
    "ProteinConstraints",
    "ProteinFailure",
    "ProteinLifecycle",
    "ProteinState",
    "SignalPayload",
    "SignalScope",
    "SignalType",
    "validate_transition",
]
