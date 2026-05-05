# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protocol attachment semantics for executable lab handoffs."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics_lab.design import (
    BatchRandomizationPlan,
    CarryoverRiskAdvisory,
    ExperimentDesignValidationReport,
    FractionationPlan,
    MultiplexLabelingPlan,
    SpikeInQcSamplePlan,
)


class SamplePreparationMetadata(JsonModel):
    """Sample-preparation context that should travel with lab planning."""

    model_config = ConfigDict(extra="forbid")

    protocol_id: str = Field(..., min_length=1)
    digestion_protocol: str = Field(..., min_length=1)
    cleanup_method: str = Field(..., min_length=1)
    fractionation_strategy: str | None = None
    labeling_strategy: str | None = None
    enrichment_strategy: str | None = None
    spike_in_strategy: str | None = None
    operator: str | None = None
    notes: tuple[str, ...] = Field(default_factory=tuple)


class InstrumentMethodMetadata(JsonModel):
    """Instrument-method context required for reviewable execution plans."""

    model_config = ConfigDict(extra="forbid")

    method_id: str = Field(..., min_length=1)
    instrument: str = Field(..., min_length=1)
    acquisition_mode: str = Field(..., min_length=1)
    gradient_minutes: float = Field(..., gt=0.0)
    ms1_resolution: int = Field(..., ge=1)
    ms2_resolution: int | None = Field(default=None, ge=1)
    collision_energy: float = Field(..., gt=0.0)
    fragmentation_method: str = Field(default="HCD", min_length=1)
    isolation_window_mz: float | None = Field(default=None, gt=0.0)
    ion_mobility_enabled: bool = False
    notes: tuple[str, ...] = Field(default_factory=tuple)


class ProtocolControlRequirement(JsonModel):
    """Control that must be present before the protocol is responsible to run."""

    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    required_sample_kind: str | None = Field(default=None, min_length=1)
    failure_if_missing: str = Field(..., min_length=1)


class ProtocolFailureCaveat(JsonModel):
    """Failure mode that should remain visible in the handoff packet."""

    model_config = ConfigDict(extra="forbid")

    caveat_id: str = Field(..., min_length=1)
    triggering_condition: str = Field(..., min_length=1)
    operational_effect: str = Field(..., min_length=1)
    mitigation: str = Field(..., min_length=1)


class LabProtocolAttachment(JsonModel):
    """Versioned protocol attachment carried with the executable lab packet."""

    model_config = ConfigDict(extra="forbid")

    protocol_id: str = Field(..., min_length=1)
    protocol_version: str = Field(..., min_length=1)
    method_id: str = Field(..., min_length=1)
    required_controls: tuple[ProtocolControlRequirement, ...] = Field(
        default_factory=tuple
    )
    failure_caveats: tuple[ProtocolFailureCaveat, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class LabProtocolEvidenceBundle(JsonModel):
    """Reviewable evidence bundle for lab protocol intent and planning."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab")
    )
    bundle_id: str = Field(..., min_length=1)
    protocol_attachment: LabProtocolAttachment
    sample_preparation: SamplePreparationMetadata
    instrument_method: InstrumentMethodMetadata
    design_validation: ExperimentDesignValidationReport
    randomization_plan: BatchRandomizationPlan
    fractionation_plan: FractionationPlan
    multiplex_plan: MultiplexLabelingPlan | None = None
    qc_plan: SpikeInQcSamplePlan | None = None
    carryover_advisory: CarryoverRiskAdvisory | None = None


def build_protocol_attachment(
    *,
    sample_preparation: SamplePreparationMetadata,
    instrument_method: InstrumentMethodMetadata,
    protocol_version: str,
    required_controls: tuple[ProtocolControlRequirement, ...],
    failure_caveats: tuple[ProtocolFailureCaveat, ...],
    notes: tuple[str, ...] = (),
) -> LabProtocolAttachment:
    """Build a versioned protocol attachment with explicit control and caveat state."""
    if not required_controls:
        raise ValueError("protocol attachments require at least one control")
    if not failure_caveats:
        raise ValueError("protocol attachments require at least one failure caveat")
    return LabProtocolAttachment(
        protocol_id=sample_preparation.protocol_id,
        protocol_version=protocol_version,
        method_id=instrument_method.method_id,
        required_controls=required_controls,
        failure_caveats=failure_caveats,
        notes=notes,
    )


def build_lab_protocol_evidence_bundle(
    *,
    bundle_id: str,
    protocol_attachment: LabProtocolAttachment,
    sample_preparation: SamplePreparationMetadata,
    instrument_method: InstrumentMethodMetadata,
    design_validation: ExperimentDesignValidationReport,
    randomization_plan: BatchRandomizationPlan,
    fractionation_plan: FractionationPlan,
    multiplex_plan: MultiplexLabelingPlan | None = None,
    qc_plan: SpikeInQcSamplePlan | None = None,
    carryover_advisory: CarryoverRiskAdvisory | None = None,
) -> LabProtocolEvidenceBundle:
    """Bundle protocol-planning evidence into one reviewable payload."""
    return LabProtocolEvidenceBundle(
        bundle_id=bundle_id,
        protocol_attachment=protocol_attachment,
        sample_preparation=sample_preparation,
        instrument_method=instrument_method,
        design_validation=design_validation,
        randomization_plan=randomization_plan,
        fractionation_plan=fractionation_plan,
        multiplex_plan=multiplex_plan,
        qc_plan=qc_plan,
        carryover_advisory=carryover_advisory,
    )


__all__ = [
    "InstrumentMethodMetadata",
    "LabProtocolAttachment",
    "LabProtocolEvidenceBundle",
    "ProtocolControlRequirement",
    "ProtocolFailureCaveat",
    "SamplePreparationMetadata",
    "build_lab_protocol_evidence_bundle",
    "build_protocol_attachment",
]
