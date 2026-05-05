# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Export and plan-comparison owners for lab handoff delivery."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, DocumentSchema, JsonModel
from bijux_proteomics_lab.design.protocols import LabProtocolAttachment
from bijux_proteomics_lab.planning import LabExecutionRequest

from .explanations import HandoffExplanation


class LimsFieldMapping(JsonModel):
    """One explicit mapping from lab surfaces into a LIMS export field."""

    model_config = ConfigDict(extra="forbid")

    source_field: str = Field(..., min_length=1)
    destination_field: str = Field(..., min_length=1)
    required: bool = True
    lossy: bool = False
    loss_note: str | None = Field(default=None, min_length=1)


class LimsExportRecord(JsonModel):
    """One LIMS-oriented export record for execution handoff."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    assay_ids: tuple[AssayId, ...] = Field(default_factory=tuple)
    instruction_ids: tuple[str, ...] = Field(default_factory=tuple)
    protocol_id: str = Field(..., min_length=1)
    protocol_version: str = Field(..., min_length=1)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)
    readiness_state: str = Field(..., min_length=1)
    blocked_reasons: tuple[str, ...] = Field(default_factory=tuple)
    scientific_rationale: tuple[str, ...] = Field(default_factory=tuple)


class LimsExportBundle(JsonModel):
    """Reviewable LIMS export bundle with field mapping and loss reporting."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab")
    )
    bundle_id: str = Field(..., min_length=1)
    system_name: str = Field(..., min_length=1)
    field_mappings: tuple[LimsFieldMapping, ...] = Field(default_factory=tuple)
    records: tuple[LimsExportRecord, ...] = Field(default_factory=tuple)
    lossy_fields: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class AlternativeAssayPlanOption(JsonModel):
    """One alternative assay-plan option for follow-up review."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(..., min_length=1)
    prioritized_assay_ids: tuple[AssayId, ...] = Field(default_factory=tuple)
    evidence_gain_score: float = Field(..., ge=0.0, le=1.0)
    estimated_cost: float = Field(..., ge=0.0)
    turnaround_days: float = Field(..., ge=0.0)
    supporting_rationale: tuple[str, ...] = Field(default_factory=tuple)


class AlternativeAssayPlanComparison(JsonModel):
    """Tradeoff comparison across alternative assay plans."""

    model_config = ConfigDict(extra="forbid")

    recommended_plan_id: str = Field(..., min_length=1)
    options: tuple[AlternativeAssayPlanOption, ...] = Field(default_factory=tuple)
    scores: tuple[tuple[str, float], ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_lims_export_bundle(
    *,
    bundle_id: str,
    system_name: str,
    candidate_id: str,
    execution_request: LabExecutionRequest,
    protocol_attachment: LabProtocolAttachment,
    explanation: HandoffExplanation,
) -> LimsExportBundle:
    """Build a LIMS-oriented export bundle with explicit field mapping and loss notes."""
    field_mappings = (
        LimsFieldMapping(
            source_field="candidate_id",
            destination_field="lims_candidate_id",
        ),
        LimsFieldMapping(
            source_field="batch_id",
            destination_field="lims_batch_id",
        ),
        LimsFieldMapping(
            source_field="requested_assay_ids",
            destination_field="lims_assay_ids",
        ),
        LimsFieldMapping(
            source_field="requested_instruction_ids",
            destination_field="lims_instruction_ids",
        ),
        LimsFieldMapping(
            source_field="scientific_rationale",
            destination_field="lims_operator_notes",
            lossy=True,
            loss_note="multiple rationale items are flattened into one operator-facing note channel",
        ),
        LimsFieldMapping(
            source_field="required_controls",
            destination_field="lims_required_controls",
        ),
    )
    lossy_fields = tuple(
        mapping.source_field for mapping in field_mappings if mapping.lossy
    )
    record = LimsExportRecord(
        candidate_id=candidate_id,
        batch_id=execution_request.batch_id,
        assay_ids=tuple(execution_request.requested_assay_ids),
        instruction_ids=tuple(execution_request.requested_instruction_ids),
        protocol_id=protocol_attachment.protocol_id,
        protocol_version=protocol_attachment.protocol_version,
        required_controls=tuple(
            sorted(
                control.control_id for control in protocol_attachment.required_controls
            )
        ),
        readiness_state=(
            "ready_for_review" if execution_request.ready_for_lab_review else "blocked"
        ),
        blocked_reasons=tuple(execution_request.unresolved_risks),
        scientific_rationale=tuple(execution_request.scientific_rationale),
    )
    notes = (
        explanation.summary,
        *(
            mapping.loss_note
            for mapping in field_mappings
            if mapping.loss_note is not None
        ),
    )
    return LimsExportBundle(
        bundle_id=bundle_id,
        system_name=system_name,
        field_mappings=field_mappings,
        records=(record,),
        lossy_fields=lossy_fields,
        notes=notes,
    )


def compare_alternative_assay_plans(
    options: tuple[AlternativeAssayPlanOption, ...],
) -> AlternativeAssayPlanComparison:
    """Compare alternative assay plans across evidence gain, cost, and turnaround."""
    scored_options = [
        (
            option.plan_id,
            round(
                max(
                    0.0,
                    option.evidence_gain_score * 0.6
                    + max(0.0, 1.0 - min(option.estimated_cost / 5.0, 1.0)) * 0.2
                    + max(0.0, 1.0 - min(option.turnaround_days / 14.0, 1.0)) * 0.2,
                ),
                4,
            ),
        )
        for option in options
    ]
    scored_options.sort(key=lambda item: (-item[1], item[0]))
    best_plan_id = scored_options[0][0] if scored_options else ""
    notes = (
        (
            "comparison favors the strongest evidence gain that still fits practical cost and turnaround",
        )
        if scored_options
        else ("no assay plan options were provided",)
    )
    return AlternativeAssayPlanComparison(
        recommended_plan_id=best_plan_id,
        options=options,
        scores=tuple(scored_options),
        notes=notes,
    )


__all__ = [
    "AlternativeAssayPlanComparison",
    "AlternativeAssayPlanOption",
    "LimsExportBundle",
    "LimsExportRecord",
    "LimsFieldMapping",
    "build_lims_export_bundle",
    "compare_alternative_assay_plans",
]
