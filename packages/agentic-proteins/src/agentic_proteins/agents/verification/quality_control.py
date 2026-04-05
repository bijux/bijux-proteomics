# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Quality control agent contract."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from agentic_proteins.agents.base import AgentRole
from agentic_proteins.agents.schemas import (
    AgentMetadata,
    QualityControlAgentInput,
    QualityControlAgentOutput,
)
from agentic_proteins.domain.metrics.quality import QCStatus
from agentic_proteins.memory.schemas import MemoryScope
from agentic_proteins.validation.agents import validate_agent


class QualityControlAgent(AgentRole):
    """QualityControlAgent."""

    name: ClassVar[str] = "quality_control"
    capabilities: ClassVar[set[str]] = {"confidence evaluation", "metric aggregation"}
    allowed_tools: ClassVar[set[str]] = {"metric_aggregator", "confidence_estimator"}
    cost_budget: ClassVar[float] = 1.0
    latency_budget_ms: ClassVar[int] = 1
    input_model: ClassVar[type[BaseModel]] = QualityControlAgentInput
    output_model: ClassVar[type[BaseModel]] = QualityControlAgentOutput
    read_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}
    write_scopes: ClassVar[set[MemoryScope]] = {MemoryScope.SESSION}

    @classmethod
    def input_schema(cls) -> dict:
        """input_schema."""
        return QualityControlAgentInput.model_json_schema()

    @classmethod
    def output_schema(cls) -> dict:
        """output_schema."""
        return QualityControlAgentOutput.model_json_schema()

    @classmethod
    def metadata(cls) -> AgentMetadata:
        """metadata."""
        return AgentMetadata(
            agent_name=cls.name,
            version="1.0",
            capabilities=sorted(cls.capabilities),
            allowed_tools=sorted(cls.allowed_tools),
            cost_budget=cls.cost_budget,
            latency_budget_ms=cls.latency_budget_ms,
            read_scopes=sorted(cls.read_scopes, key=lambda item: item.value),
            write_scopes=sorted(cls.write_scopes, key=lambda item: item.value),
        )

    def decide(self, payload: BaseModel) -> QualityControlAgentOutput:
        """decide."""
        qc_input = QualityControlAgentInput.model_validate(payload)
        validate_agent(type(self))
        candidate = qc_input.candidate
        metrics = candidate.metrics
        mean_plddt = float(metrics.get("mean_plddt", 0.0))
        helix_pct = float(metrics.get("helix_pct", 0.0))
        sheet_pct = float(metrics.get("sheet_pct", 0.0))
        structured_pct = helix_pct + sheet_pct

        violations: list[str] = []
        if structured_pct < 25.0:
            violations.append("excessive_disorder")
        if structured_pct < 15.0 and len(candidate.sequence) >= 150:
            violations.append("broken_domains")
        if mean_plddt < 60.0:
            violations.append("low_confidence_core")

        if violations:
            status = QCStatus.REJECT
        elif structured_pct < 40.0 or mean_plddt < 75.0:
            status = QCStatus.NEEDS_HUMAN
        else:
            status = QCStatus.ACCEPTABLE

        return QualityControlAgentOutput(
            status=status,
            confidence_deltas=[],
            constraint_violations=violations,
        )


QualityControlAgent.decide.__annotations__["return"] = QualityControlAgentOutput
