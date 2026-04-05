"""Biology-inspired agentic abstractions."""

from __future__ import annotations

from agentic_proteins.biology.pathway import (
    ExecutionMode,
    PathwayContract,
    PathwayExecutor,
)
from agentic_proteins.biology.protein_agent import (
    FailureEvent,
    ProteinAgent,
    ProteinConstraints,
    ProteinFailure,
    ProteinLifecycle,
    ProteinState,
)
from agentic_proteins.biology.regulator import (
    ApprovalMode,
    LLMAction,
    LLMAuthorityBoundary,
    LLMFailureMode,
    LLMObservation,
    LLMRegulator,
    PermissionMode,
    Proposal,
)
from agentic_proteins.biology.signals import SignalPayload, SignalScope, SignalType
from agentic_proteins.biology.validation import validate_transition
from agentic_proteins.core.stability import sealed

sealed()

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
