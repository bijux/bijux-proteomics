# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structured program context models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProgramPortfolioContext(BaseModel):
    """Portfolio-level framing for a program."""

    model_config = ConfigDict(extra="forbid")

    therapeutic_area: str | None = Field(
        default=None,
        min_length=1,
        description="Therapeutic area the program belongs to.",
    )
    disease_area: str | None = Field(
        default=None,
        min_length=1,
        description="Disease or indication focus.",
    )
    modality: str | None = Field(
        default=None,
        min_length=1,
        description="Protein modality or product framing.",
    )


class ProgramDeliveryContext(BaseModel):
    """Operational ownership and execution setting for a program."""

    model_config = ConfigDict(extra="forbid")

    sponsor: str | None = Field(
        default=None,
        min_length=1,
        description="Sponsoring team or organization.",
    )
    decision_horizon: str | None = Field(
        default=None,
        min_length=1,
        description="Expected timing for the next major progression decision.",
    )
    intended_output: str | None = Field(
        default=None,
        min_length=1,
        description="Expected package or deliverable from the current cycle.",
    )


class ProgramContext(BaseModel):
    """Typed context that explains why and how a program exists."""

    model_config = ConfigDict(extra="forbid")

    portfolio: ProgramPortfolioContext = Field(
        default_factory=ProgramPortfolioContext,
        description="Portfolio framing for the program.",
    )
    delivery: ProgramDeliveryContext = Field(
        default_factory=ProgramDeliveryContext,
        description="Delivery and ownership framing for the program.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Durable contextual tags for grouping and filtering.",
    )
