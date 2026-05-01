# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""External credibility and ecosystem-fit surfaces for iteration 20."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class TrialIssueEntry(JsonModel):
    """One precise issue filed by a trial user."""

    model_config = ConfigDict(extra="forbid")

    issue_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    evidence_pointer: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)


class ExternalDdaTrialInput(JsonModel):
    """Input payload for external strong-user DDA trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalDdaTrialReport(JsonModel):
    """Report for external strong-user DDA trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_dda_trial_report(
    payload: ExternalDdaTrialInput,
) -> ExternalDdaTrialReport:
    """Build DDA external trial report and require explicit issue evidence pointers."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"dda-import", "qc", "evidence", "review"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalDdaTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        dataset_id=payload.dataset_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalDiaTrialInput(JsonModel):
    """Input payload for external strong-user DIA trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalDiaTrialReport(JsonModel):
    """Report for external strong-user DIA trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_dia_trial_report(
    payload: ExternalDiaTrialInput,
) -> ExternalDiaTrialReport:
    """Build DIA external trial report and require explicit issue evidence pointers."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"dia-import", "quant", "qc", "evidence"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalDiaTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        dataset_id=payload.dataset_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalQuantTrialInput(JsonModel):
    """Input payload for external strong-user quant trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    mini_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalQuantTrialReport(JsonModel):
    """Report for external strong-user quant trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    mini_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_quant_trial_report(
    payload: ExternalQuantTrialInput,
) -> ExternalQuantTrialReport:
    """Build quant external trial report for normalization/DA/review coverage."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"normalization", "differential-abundance", "review"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalQuantTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        mini_study_id=payload.mini_study_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )


class ExternalPtmTrialInput(JsonModel):
    """Input payload for external strong-user PTM trial reporting."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    ptm_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)


class ExternalPtmTrialReport(JsonModel):
    """Report for external strong-user PTM trial execution and issue quality."""

    model_config = ConfigDict(extra="forbid")

    trial_id: str = Field(..., min_length=1)
    external_user_id: str = Field(..., min_length=1)
    ptm_study_id: str = Field(..., min_length=1)
    executed_steps: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[TrialIssueEntry, ...] = Field(default_factory=tuple)
    precise_issue_count: int = Field(..., ge=0)
    trial_completed: bool


def build_external_strong_user_ptm_trial_report(
    payload: ExternalPtmTrialInput,
) -> ExternalPtmTrialReport:
    """Build PTM external trial report for ambiguity inspection and lab handoff."""

    precise_issues = tuple(
        issue for issue in payload.issues if issue.evidence_pointer.strip()
    )
    required_steps = {"ptm-ambiguity-review", "lab-handoff"}
    completed = required_steps.issubset(set(payload.executed_steps))
    return ExternalPtmTrialReport(
        trial_id=payload.trial_id,
        external_user_id=payload.external_user_id,
        ptm_study_id=payload.ptm_study_id,
        executed_steps=tuple(payload.executed_steps),
        issues=tuple(payload.issues),
        precise_issue_count=len(precise_issues),
        trial_completed=completed,
    )
