# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Domain conflict and untrustworthy-result surfaces for workflow review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.review.explanations.scientific_story import WorkflowScientificSnapshot
from bijux_proteomics_foundation import JsonModel


class ScientificWorkflowFamily(StrEnum):
    """Core scientific families that must publish distrust triggers explicitly."""

    DIGESTION = "digestion"
    IDENTIFICATION = "identification"
    QUANTIFICATION = "quantification"
    PTM = "ptm"
    QC = "qc"
    REVIEW_PROJECTION = "review_projection"


class UntrustworthyChecklistEntry(JsonModel):
    """One trigger that should make the corresponding family less trusted."""

    model_config = ConfigDict(extra="forbid")

    entry_id: str = Field(..., min_length=1)
    family: ScientificWorkflowFamily
    trigger: str = Field(..., min_length=1)
    consequence: str = Field(..., min_length=1)
    blocking: bool


class ScientificUntrustworthyChecklist(JsonModel):
    """Checklist of distrust triggers for one scientific family."""

    model_config = ConfigDict(extra="forbid")

    family: ScientificWorkflowFamily
    entries: tuple[UntrustworthyChecklistEntry, ...] = Field(default_factory=tuple)


class ScientificConflictFindingCode(StrEnum):
    """Cross-family conflict surfaces that deserve explicit review."""

    TARGET_DECOY_COLLISION = "target_decoy_collision"
    SHARED_PEPTIDE_PRESSURE = "shared_peptide_pressure"
    MISSING_CHANNEL_PRESSURE = "missing_channel_pressure"
    AMBIGUOUS_PTM_LOCALIZATION = "ambiguous_ptm_localization"
    EXTERNAL_ENGINE_DISAGREEMENT = "external_engine_disagreement"


class ScientificConflictFinding(JsonModel):
    """One domain conflict with a reviewer-facing consequence."""

    model_config = ConfigDict(extra="forbid")

    code: ScientificConflictFindingCode
    severity: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    blocks_decision_grade: bool


class ScientificConflictReport(JsonModel):
    """Conflict pressure across core workflow families."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    findings: tuple[ScientificConflictFinding, ...] = Field(default_factory=tuple)


def build_scientific_untrustworthy_checklists() -> tuple[
    ScientificUntrustworthyChecklist, ...
]:
    """Return explicit distrust triggers for the biggest scientific families."""

    return (
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.DIGESTION,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="digestion-empty-space",
                    family=ScientificWorkflowFamily.DIGESTION,
                    trigger="no peptides survive digestion",
                    consequence="all downstream identification evidence becomes structurally unsupported",
                    blocking=True,
                ),
            ),
        ),
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.IDENTIFICATION,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="identification-target-decoy-collision",
                    family=ScientificWorkflowFamily.IDENTIFICATION,
                    trigger="target and decoy namespaces collide",
                    consequence="FDR trust collapses and protein promotion must stop",
                    blocking=True,
                ),
                UntrustworthyChecklistEntry(
                    entry_id="identification-shared-peptide-pressure",
                    family=ScientificWorkflowFamily.IDENTIFICATION,
                    trigger="shared peptide groups dominate without explicit disclosure",
                    consequence="protein-level claims become easy to overread",
                    blocking=False,
                ),
            ),
        ),
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.QUANTIFICATION,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="quantification-missing-channel-pressure",
                    family=ScientificWorkflowFamily.QUANTIFICATION,
                    trigger="missing quantitative support dominates the bundle",
                    consequence="quantitative conclusions remain review-grade only",
                    blocking=True,
                ),
            ),
        ),
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.PTM,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="ptm-ambiguous-localization",
                    family=ScientificWorkflowFamily.PTM,
                    trigger="site-level ambiguity remains unresolved",
                    consequence="PTM evidence stays interpretive rather than targetable",
                    blocking=True,
                ),
            ),
        ),
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.QC,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="qc-blocking-issues",
                    family=ScientificWorkflowFamily.QC,
                    trigger="blocking QC issues remain open",
                    consequence="decision-grade promotion is scientifically irresponsible",
                    blocking=True,
                ),
            ),
        ),
        ScientificUntrustworthyChecklist(
            family=ScientificWorkflowFamily.REVIEW_PROJECTION,
            entries=(
                UntrustworthyChecklistEntry(
                    entry_id="review-projection-engine-disagreement",
                    family=ScientificWorkflowFamily.REVIEW_PROJECTION,
                    trigger="external-engine disagreement remains unresolved at promotion time",
                    consequence="review projection must expose disagreement instead of flattening it",
                    blocking=False,
                ),
            ),
        ),
    )


def evaluate_domain_conflicts(
    snapshot: WorkflowScientificSnapshot,
) -> ScientificConflictReport:
    """Return explicit conflict findings for the hardest domain-level clashes."""

    findings: list[ScientificConflictFinding] = []
    if snapshot.target_decoy_collision_count > 0:
        findings.append(
            ScientificConflictFinding(
                code=ScientificConflictFindingCode.TARGET_DECOY_COLLISION,
                severity="high",
                rationale="target-decoy collisions invalidate the separation needed for trusted FDR accounting",
                blocks_decision_grade=True,
            )
        )
    if snapshot.shared_peptide_group_count > 0:
        findings.append(
            ScientificConflictFinding(
                code=ScientificConflictFindingCode.SHARED_PEPTIDE_PRESSURE,
                severity="medium",
                rationale="shared peptide groups require explicit protein-level caution even when the workflow remains usable",
                blocks_decision_grade=False,
            )
        )
    if snapshot.quant_missingness_fraction > 0.0:
        findings.append(
            ScientificConflictFinding(
                code=ScientificConflictFindingCode.MISSING_CHANNEL_PRESSURE,
                severity="high"
                if snapshot.quant_missingness_fraction > 0.5
                else "medium",
                rationale="missing quantitative support changes how confidently downstream effect sizes can be read",
                blocks_decision_grade=snapshot.quant_missingness_fraction > 0.5,
            )
        )
    if snapshot.ambiguous_ptm_site_count > 0:
        findings.append(
            ScientificConflictFinding(
                code=ScientificConflictFindingCode.AMBIGUOUS_PTM_LOCALIZATION,
                severity="high",
                rationale="ambiguous PTM localization must stay visible because it changes lab targetability",
                blocks_decision_grade=True,
            )
        )
    if snapshot.external_engine_disagreement_count > 0:
        findings.append(
            ScientificConflictFinding(
                code=ScientificConflictFindingCode.EXTERNAL_ENGINE_DISAGREEMENT,
                severity="medium",
                rationale="external-engine disagreement is a scientific conflict, not a cosmetic import mismatch",
                blocks_decision_grade=False,
            )
        )

    return ScientificConflictReport(
        workflow_id=snapshot.workflow_id,
        findings=tuple(findings),
    )
