# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Operating assumptions for protein programs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OperatingModel(BaseModel):
    """How the program moves between computation, review, and lab work."""

    model_config = ConfigDict(extra="forbid")

    review_cadence: str = Field(
        default="per-decision",
        min_length=1,
        description="When human review is expected.",
    )
    human_review_required: bool = Field(
        default=True,
        description="Whether human review is mandatory before progression.",
    )
    lab_feedback_required: bool = Field(
        default=True,
        description="Whether lab results must close the loop before iteration.",
    )
    decision_owner_roles: list[str] = Field(
        default_factory=lambda: ["scientist"],
        description="Roles accountable for final progression decisions.",
    )
