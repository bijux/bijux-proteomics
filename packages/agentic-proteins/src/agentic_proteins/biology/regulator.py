"""LLM regulator for parameter tuning only."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from agentic_proteins.biology.protein_agent import ProteinAgent
from agentic_proteins.biology.signals import SignalPayload

if False:  # pragma: no cover - type checking only
    from agentic_proteins.biology.pathway import PathwayContract, PathwayExecutor


class LLMAction(str, Enum):
    """Allowed LLM actions for tuning only."""

    TUNE_PROBABILITY = "tune_probability"
    ADJUST_THRESHOLD = "adjust_threshold"
    SUGGEST_WEIGHT = "suggest_weight"


class LLMFailureMode(str, Enum):
    """LLM failure modes treated as sensor faults."""

    HALLUCINATION = "hallucination"
    OVERCONFIDENCE = "overconfidence"
    INCONSISTENCY = "inconsistency"
    DRIFT = "drift"


class ApprovalMode(str, Enum):
    """Human-in-the-loop approval modes."""

    AUTO_APPROVE = "auto_approve"
    MANUAL_APPROVE = "manual_approve"
    AUTO_REJECT = "auto_reject"


class PermissionMode(str, Enum):
    """Authority permission modes."""

    READ_ONLY = "read_only"
    WRITE_THROUGH = "write_through"


@dataclass(frozen=True)
class LLMAuthorityBoundary:
    """Authority boundary for LLM actions."""

    allowed_actions: tuple[LLMAction, ...]
    forbidden_actions: tuple[LLMAction, ...]
    permission: PermissionMode

    def assert_allowed(self, action: LLMAction) -> None:
        if action in self.forbidden_actions:
            raise ValueError("LLM action is forbidden.")
        if action not in self.allowed_actions:
            raise ValueError("LLM action is not allowed.")


@dataclass(frozen=True)
class Proposal:
    """Structured proposal payload."""

    target: str
    parameter: str
    suggested_change: float
    confidence: float
    rationale: str
    action: LLMAction


@dataclass(frozen=True)
class LLMObservation:
    """Observability record for LLM decisions."""

    prompt: str
    model: str
    temperature: float
    proposal: Proposal | None
    accepted: bool


@dataclass
class LLMRegulator:
    """Meta-controller that never enforces transitions."""

    model_id: str
    temperature: float = 0.0
    authority: LLMAuthorityBoundary | None = None
    approval_mode: ApprovalMode = ApprovalMode.AUTO_APPROVE
    approval_hook: Callable[[Proposal], bool] | None = None
    failure_modes: list[LLMFailureMode] = None  # type: ignore[assignment]
    observations: list[LLMObservation] = None  # type: ignore[assignment]
    prompt_log: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.failure_modes is None:
            self.failure_modes = []
        if self.observations is None:
            self.observations = []
        if self.prompt_log is None:
            self.prompt_log = []
        if self.authority is None:
            self.authority = LLMAuthorityBoundary(
                allowed_actions=(
                    LLMAction.TUNE_PROBABILITY,
                    LLMAction.ADJUST_THRESHOLD,
                    LLMAction.SUGGEST_WEIGHT,
                ),
                forbidden_actions=(),
                permission=PermissionMode.READ_ONLY,
            )

    def propose(self, prompt: str, proposal: Proposal | None) -> Proposal | None:
        self.prompt_log.append(prompt)
        if proposal is None:
            self.observations.append(
                LLMObservation(
                    prompt=prompt,
                    model=self.model_id,
                    temperature=self.temperature,
                    proposal=None,
                    accepted=False,
                )
            )
            return None
        self.authority.assert_allowed(proposal.action)
        return proposal

    def validate_proposal(
        self,
        proposal: Proposal,
        *,
        agent: ProteinAgent,
        contract: PathwayContract,
    ) -> bool:
        if proposal.parameter not in agent.tunable_parameters():
            return False
        if proposal.action not in self.authority.allowed_actions:
            return False
        if proposal.confidence < 0.0 or proposal.confidence > 1.0:
            return False
        _ = contract
        return True

    def counterfactual_acceptance(
        self,
        proposal: Proposal,
        *,
        executor: PathwayExecutor,
        signals: Sequence[SignalPayload],
        metric: Callable[[Sequence[Any]], float],
    ) -> bool:
        baseline = executor.replay(list(signals))
        baseline_score = metric(baseline)
        simulated = executor.replay_with_adjustments(
            list(signals), {proposal.target: proposal}
        )
        simulated_score = metric(simulated)
        return simulated_score > baseline_score

    def approve(self, proposal: Proposal) -> bool:
        if self.approval_mode is ApprovalMode.AUTO_REJECT:
            return False
        if self.approval_mode is ApprovalMode.AUTO_APPROVE:
            return True
        if self.approval_hook is None:
            raise ValueError("Manual approval requires a hook.")
        return self.approval_hook(proposal)

    def apply(
        self,
        proposal: Proposal,
        *,
        agent: ProteinAgent,
    ) -> bool:
        if self.authority.permission is PermissionMode.READ_ONLY:
            raise ValueError("LLM write-through is forbidden.")
        self.authority.assert_allowed(proposal.action)
        if proposal.parameter == "transition_probabilities":
            if not agent.inputs:
                return False
            agent.transition_probabilities[
                (agent.internal_state, agent.inputs[-1].signal_type)
            ] = proposal.suggested_change
        elif proposal.parameter == "noise_sigma":
            agent.noise_sigma = proposal.suggested_change
        elif proposal.parameter == "energy_cost":
            agent.constraints = agent.constraints.__class__(
                energy_cost=proposal.suggested_change,
                resource_dependency=agent.constraints.resource_dependency,
                inhibition_conditions=agent.constraints.inhibition_conditions,
                min_energy=agent.constraints.min_energy,
            )
        else:
            return False
        return True

    def observe(
        self,
        *,
        prompt: str,
        proposal: Proposal | None,
        accepted: bool,
    ) -> None:
        self.observations.append(
            LLMObservation(
                prompt=prompt,
                model=self.model_id,
                temperature=self.temperature,
                proposal=proposal,
                accepted=accepted,
            )
        )
