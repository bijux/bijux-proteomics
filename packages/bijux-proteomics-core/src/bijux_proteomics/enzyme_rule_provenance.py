# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Enzyme-rule provenance contracts for digestion policy transparency."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.digestion import PeptideDigestionMode, ProteaseRule
from bijux_proteomics_foundation import JsonModel


class EnzymeRuleSupportState(StrEnum):
    """Support classification for one digestion-rule provenance record."""

    SUPPORTED = "supported"
    ADVISORY = "advisory"
    UNSUPPORTED = "unsupported"


class EnzymeRuleProvenance(JsonModel):
    """Provenance snapshot over a protease rule and digestion mode."""

    model_config = ConfigDict(extra="forbid")

    rule_name: str = Field(..., min_length=1)
    cleavage_mode: str = Field(..., min_length=1)
    cleavage_residues: str = Field(..., min_length=1)
    blocked_by_next: str = ""
    blocked_by_previous: str = ""
    digestion_mode: PeptideDigestionMode
    support_state: EnzymeRuleSupportState
    source: str = Field(..., min_length=1)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_enzyme_rule_provenance(
    *,
    rule: ProteaseRule,
    digestion_mode: PeptideDigestionMode,
    source: str,
    unsupported_reason: str | None = None,
) -> EnzymeRuleProvenance:
    """Build a provenance record for built-in, custom, or semi-specific enzyme use."""
    notes: list[str] = []
    support_state = EnzymeRuleSupportState.SUPPORTED
    if digestion_mode is PeptideDigestionMode.SEMI_SPECIFIC:
        notes.append(
            "semi-specific digestion is advisory for strict cross-protease comparability"
        )
        support_state = EnzymeRuleSupportState.ADVISORY
    if digestion_mode is PeptideDigestionMode.NON_SPECIFIC:
        notes.append(
            "non-specific digestion is exploratory and should remain separated from enzyme-specific evidence"
        )
        support_state = EnzymeRuleSupportState.ADVISORY
    if unsupported_reason:
        notes.append(unsupported_reason)
        support_state = EnzymeRuleSupportState.UNSUPPORTED
    return EnzymeRuleProvenance(
        rule_name=rule.name,
        cleavage_mode=rule.cleavage_mode.value,
        cleavage_residues=rule.cleavage_residues,
        blocked_by_next=rule.blocked_by_next,
        blocked_by_previous=rule.blocked_by_previous,
        digestion_mode=digestion_mode,
        support_state=support_state,
        source=source.strip(),
        notes=tuple(notes),
    )
