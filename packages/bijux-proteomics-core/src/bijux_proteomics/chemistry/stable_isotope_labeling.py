# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Stable isotope labeling models for SILAC/TMT/iTRAQ quantification."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics_foundation import JsonModel


class StableIsotopeLabelChemistry(StrEnum):
    """Supported stable-isotope labeling chemistry families."""

    SILAC = "silac"
    TMT = "tmt"
    ITRAQ = "itraq"


class StableIsotopeLabelChannel(JsonModel):
    """One quantification channel in a labeling design."""

    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    label_name: str = Field(..., min_length=1)
    reporter_mz: float | None = Field(default=None, gt=0.0)
    normalization_group: str = Field(..., min_length=1)
    role: str = Field(default="sample", min_length=1)


class StableIsotopeLabelingModel(JsonModel):
    """Stable-isotope labeling model with channel and quantification rules."""

    model_config = ConfigDict(extra="forbid")

    chemistry: StableIsotopeLabelChemistry
    channels: tuple[StableIsotopeLabelChannel, ...] = Field(default_factory=tuple)
    quant_rule: str = Field(..., min_length=1)
    reference_channel_id: str | None = None

    @model_validator(mode="after")
    def _validate_channels(self) -> StableIsotopeLabelingModel:
        if not self.channels:
            raise ValueError(
                "stable-isotope labeling model requires at least one channel"
            )
        channel_ids = {channel.channel_id for channel in self.channels}
        if len(channel_ids) != len(self.channels):
            raise ValueError(
                "stable-isotope labeling channels must use unique channel_id values"
            )
        if self.reference_channel_id and self.reference_channel_id not in channel_ids:
            raise ValueError("reference_channel_id must point to an existing channel")
        if self.chemistry in {
            StableIsotopeLabelChemistry.TMT,
            StableIsotopeLabelChemistry.ITRAQ,
        } and any(channel.reporter_mz is None for channel in self.channels):
            raise ValueError("isobaric labeling channels require reporter_mz values")
        return self


def build_stable_isotope_labeling_model(
    *,
    chemistry: StableIsotopeLabelChemistry,
    channels: Sequence[StableIsotopeLabelChannel],
    quant_rule: str,
    reference_channel_id: str | None = None,
) -> StableIsotopeLabelingModel:
    """Build and validate a stable-isotope labeling model."""
    return StableIsotopeLabelingModel(
        chemistry=chemistry,
        channels=tuple(channels),
        quant_rule=quant_rule,
        reference_channel_id=reference_channel_id,
    )
