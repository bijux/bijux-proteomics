# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""End-to-end workflow run surfaces."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404
import tempfile
from typing import Any, Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats.proteomics_formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.io.ingestion import parse_chromatogram_qc_table
from bijux_proteomics.io.spectra import MgfParseReport, parse_mgf
from bijux_proteomics.ptm import (
    build_ptm_motif_windows,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_ptm_lab_validation_packet,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.quantification import (
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MultiplexNormalizationPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_based_quant_bundle,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.contracts.input_models import Ms1FeatureRecord
from bijux_proteomics.quantification.review import (
    build_multiplex_channel_balance_diagnostics_report,
    build_quant_review_bundle,
)
from bijux_proteomics.sequences.core import (
    DecoyGenerationMode,
    FastaParseMode,
    generate_decoy_records,
    parse_fasta_document,
)
from bijux_proteomics.sequences.digestion import digest_protein_records
from bijux_proteomics_runtime.artifacts import StepArtifact, build_step_artifact
from bijux_proteomics_foundation import JsonModel


class _PtmLabValidationEntryLike(Protocol):
    """Shape runtime needs from one PTM lab validation entry."""

    target_peptides: tuple[str, ...]
    assay_risk: Any

    def to_dict(self) -> dict[str, Any]:
        """Serialize one entry for replay-stable hashing."""


class _PtmLabValidationPacketLike(Protocol):
    """Shape runtime needs from one PTM lab validation packet."""

    entries: tuple[_PtmLabValidationEntryLike, ...]
    unresolved_risk_count: int


class RuntimeWorkflowStatus(StrEnum):
    """Execution status for one runtime workflow report."""

    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"


class SequenceToDigestWorkflowRunReport(JsonModel):
    """End-to-end runtime report for FASTA -> digest -> decoy -> evidence."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    target_record_count: int = Field(..., ge=0)
    decoy_record_count: int = Field(..., ge=0)
    target_peptide_count: int = Field(..., ge=0)
    decoy_peptide_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DdaSearchHitInput(JsonModel):
    """Minimal normalized DDA search hit used in runtime import reports."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    score: float


class DdaImportWorkflowRunReport(JsonModel):
    """End-to-end runtime report for DDA import and inference surfaces."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    spectrum_count: int = Field(..., ge=0)
    accepted_psm_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    qc_issue_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class DiaPrecursorQuantInput(JsonModel):
    """Minimal DIA precursor-level import row."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    intensity: float | None = Field(default=None, ge=0.0)


class DiaImportWorkflowRunReport(JsonModel):
    """End-to-end runtime report for DIA import and quant evidence."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    precursor_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    quantified_precursor_count: int = Field(..., ge=0)
    qc_missing_intensity_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class QuantRuntimeWorkflowRunReport(JsonModel):
    """End-to-end runtime report for quant workflow execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    feature_record_count: int = Field(..., ge=0)
    design_entry_count: int = Field(..., ge=0)
    condition_count: int = Field(..., ge=0)
    outlier_sample_count: int = Field(..., ge=0)
    review_bundle_hash: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PtmRuntimeWorkflowRunReport(JsonModel):
    """End-to-end runtime report for PTM workflow execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    accepted_identification_count: int = Field(..., ge=0)
    mapped_site_count: int = Field(..., ge=0)
    motif_window_count: int = Field(..., ge=0)
    occupancy_entry_count: int = Field(..., ge=0)
    lab_packet_target_count: int = Field(..., ge=0)
    unresolved_risk_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class MultiplexRuntimeWorkflowRunReport(JsonModel):
    """End-to-end runtime report for multiplex quant execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    feature_record_count: int = Field(..., ge=0)
    multiplex_group_count: int = Field(..., ge=0)
    channel_count: int = Field(..., ge=0)
    reference_channel_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    flagged_imbalance_count: int = Field(..., ge=0)
    carrier_effect_channel_count: int = Field(..., ge=0)
    review_bundle_hash: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class TargetedRuntimeWorkflowRunReport(JsonModel):
    """End-to-end runtime report for targeted benchmark execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    qc_point_count: int = Field(..., ge=0)
    approved_transition_count: int = Field(..., ge=0)
    exploratory_transition_count: int = Field(..., ge=0)
    refused_transition_count: int = Field(..., ge=0)
    blocked_follow_up_count: int = Field(..., ge=0)
    observed_outcome_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class KnowledgeEvidenceInput(JsonModel):
    """One evidence item for knowledge-review workflow execution."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    trust_score: float = Field(..., ge=0.0, le=1.0)
    contradicts: tuple[str, ...] = Field(default_factory=tuple)


class KnowledgeReviewWorkflowRunReport(JsonModel):
    """End-to-end runtime report for evidence-graph knowledge review workflows."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    evidence_node_count: int = Field(..., ge=0)
    ranked_evidence_count: int = Field(..., ge=0)
    contradiction_count: int = Field(..., ge=0)
    accepted_claim_count: int = Field(..., ge=0)
    contested_claim_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class LabHandoffWorkflowRunReport(JsonModel):
    """End-to-end runtime report for lab handoff execution surfaces."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    review_target_count: int = Field(..., ge=0)
    planned_assay_count: int = Field(..., ge=0)
    unresolved_risk_count: int = Field(..., ge=0)
    export_file_count: int = Field(..., ge=0)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)
    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SimulatedExternalToolKind(StrEnum):
    """Deterministic simulated tool families used for contract testing."""

    SEARCH = "search"
    QUANT = "quant"
    QC = "qc"


class SimulatedExternalToolRunEntry(JsonModel):
    """One deterministic simulated-tool execution entry."""

    model_config = ConfigDict(extra="forbid")

    tool_kind: SimulatedExternalToolKind
    command: str = Field(..., min_length=1)
    exit_code: int
    artifact_path: str = Field(..., min_length=1)
    stdout: str = Field(..., min_length=1)


class SimulatedExternalEngineHarnessReport(JsonModel):
    """Deterministic simulated external-engine harness execution report."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    deterministic: bool
    entries: tuple[SimulatedExternalToolRunEntry, ...] = Field(default_factory=tuple)
    replay_cache_key: str = Field(..., min_length=64, max_length=64)


class LocalExternalToolRunDisposition(StrEnum):
    """Disposition of one local external-tool run."""

    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class LocalExternalToolRunReport(JsonModel):
    """Execution report for one configured local external-tool command."""

    model_config = ConfigDict(extra="forbid")

    disposition: LocalExternalToolRunDisposition
    command: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: float = Field(..., ge=0.1)
    env_overrides: dict[str, str] = Field(default_factory=dict)
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    validated_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    missing_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowReplayOutcome(StrEnum):
    """Replay/cache outcome classification for one workflow surface."""

    REUSED = "reused"
    RERUN = "rerun"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    REFUSED = "refused"


class WorkflowCacheReplayEntry(JsonModel):
    """One workflow surface outcome across repeated runtime runs."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    previous_hash: str | None = None
    current_hash: str | None = None
    outcome: WorkflowReplayOutcome
    detail: str = Field(..., min_length=1)


class WorkflowCacheReplayReport(JsonModel):
    """Cache/replay report over repeated workflow runs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowCacheReplayEntry, ...] = Field(default_factory=tuple)
    reused_count: int = Field(..., ge=0)
    rerun_count: int = Field(..., ge=0)
    changed_count: int = Field(..., ge=0)
    unchanged_count: int = Field(..., ge=0)
    refused_count: int = Field(..., ge=0)


def _stable_runtime_key(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _step_artifact(
    *,
    step_id: str,
    description: str,
    status: RuntimeWorkflowStatus,
    input_payloads: dict[str, Any],
    output_payloads: dict[str, Any],
    entity_counts: dict[str, int],
    schema_names: tuple[str, ...],
    allowed_empty_reason: str | None = None,
) -> StepArtifact:
    return build_step_artifact(
        step_id=step_id,
        description=description,
        status=status.value,
        input_payloads=input_payloads,
        output_payloads=output_payloads,
        entity_counts=entity_counts,
        schema_names=schema_names,
        allowed_empty_reason=allowed_empty_reason,
    )


def _parse_mgf_text(mgf_text: str) -> MgfParseReport:
    with tempfile.NamedTemporaryFile("w", suffix=".mgf", delete=False) as handle:
        handle.write(mgf_text)
        temp_path = Path(handle.name)
    try:
        return parse_mgf(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def _normalize_stream(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _multiplex_channel_role(
    entry: ExperimentalDesignEntry,
) -> LabelBasedChannelRole:
    if entry.sample_role is ExperimentalDesignSampleRole.POOLED_REFERENCE:
        return LabelBasedChannelRole.REFERENCE
    if entry.sample_role is ExperimentalDesignSampleRole.QC_BRIDGE:
        return LabelBasedChannelRole.QC_BRIDGE
    return LabelBasedChannelRole.SAMPLE


def _build_label_policy(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> LabelBasedQuantPolicy:
    channel_entries = tuple(
        LabelBasedChannelPolicyEntry(
            multiplex_group=entry.multiplex_group or "",
            multiplex_channel=entry.multiplex_channel or "",
            channel_role=_multiplex_channel_role(entry),
        )
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    )
    return LabelBasedQuantPolicy(
        channel_entries=channel_entries,
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
    )


def _count_transition_ids(payload: dict[str, Any], key: str) -> int:
    transition_review = payload.get("transition_review")
    if not isinstance(transition_review, dict):
        return 0
    transition_ids = transition_review.get(key, ())
    if not isinstance(transition_ids, list):
        return 0
    return len(transition_ids)


def _count_assay_outcomes(payload: dict[str, Any]) -> int:
    outcome = payload.get("outcome")
    if not isinstance(outcome, dict):
        return 0
    assay_outcomes = outcome.get("assay_outcomes", ())
    if not isinstance(assay_outcomes, list):
        return 0
    return len(assay_outcomes)


def run_sequence_to_digest_workflow_end_to_end(
    fasta_text: str,
    *,
    artifact_root: str = "artifacts/workflows/sequence-to-digest",
    decoy_mode: DecoyGenerationMode = DecoyGenerationMode.REVERSE,
) -> SequenceToDigestWorkflowRunReport:
    """Execute FASTA -> digest -> decoy -> peptide evidence end to end."""
    try:
        parse_report = parse_fasta_document(fasta_text, mode=FastaParseMode.STRICT)
    except ValueError as error:
        key = _stable_runtime_key(
            {
                "workflow": "sequence-to-digest",
                "fasta": fasta_text,
                "refusal": str(error),
            }
        )
        return SequenceToDigestWorkflowRunReport(
            workflow_id="sequence-to-digest",
            status=RuntimeWorkflowStatus.REFUSED,
            target_record_count=0,
            decoy_record_count=0,
            target_peptide_count=0,
            decoy_peptide_count=0,
            artifact_paths=(f"{artifact_root}/parse-refusal.json",),
            evidence_pointers=("fasta.parse.rejected_records",),
            replay_cache_key=key,
            steps=(
                _step_artifact(
                    step_id="parse-fasta",
                    description="parse strict FASTA records",
                    status=RuntimeWorkflowStatus.REFUSED,
                    input_payloads={
                        "fasta_text": fasta_text,
                        "parse_mode": FastaParseMode.STRICT.value,
                    },
                    output_payloads={
                        "accepted_records": (),
                        "rejected_records": (
                            {"reason": str(error)},
                        ),
                    },
                    entity_counts={"accepted_records": 0},
                    schema_names=("fasta_record", "fasta_parse_rejection"),
                    allowed_empty_reason=str(error),
                ),
            ),
            note="workflow refused because the FASTA payload could not be parsed under strict rules",
        )
    if not parse_report.accepted_records:
        key = _stable_runtime_key(
            {"workflow": "sequence-to-digest", "fasta": fasta_text}
        )
        return SequenceToDigestWorkflowRunReport(
            workflow_id="sequence-to-digest",
            status=RuntimeWorkflowStatus.REFUSED,
            target_record_count=0,
            decoy_record_count=0,
            target_peptide_count=0,
            decoy_peptide_count=0,
            artifact_paths=(f"{artifact_root}/parse-refusal.json",),
            evidence_pointers=("fasta.parse.rejected_records",),
            replay_cache_key=key,
            steps=(
                _step_artifact(
                    step_id="parse-fasta",
                    description="parse strict FASTA records",
                    status=RuntimeWorkflowStatus.REFUSED,
                    input_payloads={
                        "fasta_text": fasta_text,
                        "parse_mode": FastaParseMode.STRICT.value,
                    },
                    output_payloads={
                        "accepted_records": (),
                        "rejected_records": parse_report.rejected_records,
                    },
                    entity_counts={"accepted_records": 0},
                    schema_names=("fasta_record", "fasta_parse_rejection"),
                    allowed_empty_reason=(
                        "no FASTA records were accepted under strict parsing"
                    ),
                ),
            ),
            note="workflow refused because no FASTA records were accepted under strict parsing",
        )
    targets = parse_report.accepted_records
    decoys = generate_decoy_records(targets, mode=decoy_mode)
    target_peptides = digest_protein_records(targets, protease="trypsin", min_length=7)
    decoy_peptides = digest_protein_records(decoys, protease="trypsin", min_length=7)
    key = _stable_runtime_key(
        {
            "workflow": "sequence-to-digest",
            "target_records": len(targets),
            "decoy_records": len(decoys),
            "target_peptides": len(target_peptides),
            "decoy_peptides": len(decoy_peptides),
            "decoy_mode": decoy_mode.value,
        }
    )
    return SequenceToDigestWorkflowRunReport(
        workflow_id="sequence-to-digest",
        status=RuntimeWorkflowStatus.COMPLETED,
        target_record_count=len(targets),
        decoy_record_count=len(decoys),
        target_peptide_count=len(target_peptides),
        decoy_peptide_count=len(decoy_peptides),
        artifact_paths=(
            f"{artifact_root}/targets.fasta",
            f"{artifact_root}/decoys.fasta",
            f"{artifact_root}/peptides.tsv",
        ),
        evidence_pointers=(
            "fasta.accepted_records",
            "decoy.records",
            "digest.target_peptides",
            "digest.decoy_peptides",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="parse-fasta",
                description="parse strict FASTA records",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "fasta_text": fasta_text,
                    "parse_mode": FastaParseMode.STRICT.value,
                },
                output_payloads={"accepted_records": targets},
                entity_counts={"accepted_records": len(targets)},
                schema_names=("fasta_record",),
            ),
            _step_artifact(
                step_id="generate-decoys",
                description="generate deterministic decoy records",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "target_records": targets,
                    "decoy_mode": decoy_mode.value,
                },
                output_payloads={"decoy_records": decoys},
                entity_counts={"decoy_records": len(decoys)},
                schema_names=("decoy_fasta_record",),
            ),
            _step_artifact(
                step_id="digest-targets",
                description="digest accepted target records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "target_records": targets,
                    "protease": "trypsin",
                    "min_length": 7,
                },
                output_payloads={"target_peptides": target_peptides},
                entity_counts={"target_peptides": len(target_peptides)},
                schema_names=("digested_target_peptide",),
                allowed_empty_reason=(
                    "accepted target records may all fall outside the digestion length rule"
                ),
            ),
            _step_artifact(
                step_id="digest-decoys",
                description="digest generated decoy records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "decoy_records": decoys,
                    "protease": "trypsin",
                    "min_length": 7,
                },
                output_payloads={"decoy_peptides": decoy_peptides},
                entity_counts={"decoy_peptides": len(decoy_peptides)},
                schema_names=("digested_decoy_peptide",),
                allowed_empty_reason=(
                    "generated decoy records may all fall outside the digestion length rule"
                ),
            ),
        ),
        note="workflow completed with deterministic FASTA, decoy, and digestion evidence surfaces",
    )


def run_dda_import_workflow_end_to_end(
    mgf_text: str,
    *,
    search_hits: tuple[DdaSearchHitInput, ...],
    artifact_root: str = "artifacts/workflows/dda-import",
) -> DdaImportWorkflowRunReport:
    """Execute DDA runtime flow: spectra import -> PSM -> peptide/protein -> QC evidence."""
    mgf_report = _parse_mgf_text(mgf_text)
    spectra = {spectrum.spectrum_id for spectrum in mgf_report.accepted_spectra}
    accepted_hits = tuple(hit for hit in search_hits if hit.spectrum_id in spectra)
    rejected_hits = tuple(hit for hit in search_hits if hit.spectrum_id not in spectra)
    peptides = tuple(sorted({hit.peptide for hit in accepted_hits}))
    proteins = tuple(sorted({hit.protein_ref for hit in accepted_hits}))
    qc_issue_count = len(mgf_report.rejected_blocks) + len(rejected_hits)
    key = _stable_runtime_key(
        {
            "workflow": "dda-import",
            "spectra": len(spectra),
            "hits": [hit.to_dict() for hit in search_hits],
            "accepted_psm_count": len(accepted_hits),
        }
    )
    return DdaImportWorkflowRunReport(
        workflow_id="dda-import",
        status=RuntimeWorkflowStatus.COMPLETED,
        spectrum_count=len(spectra),
        accepted_psm_count=len(accepted_hits),
        peptide_count=len(peptides),
        protein_count=len(proteins),
        rejected_psm_count=len(rejected_hits),
        qc_issue_count=qc_issue_count,
        artifact_paths=(
            f"{artifact_root}/spectra.mgf",
            f"{artifact_root}/psm.tsv",
            f"{artifact_root}/protein_inference.tsv",
            f"{artifact_root}/qc_report.json",
        ),
        evidence_pointers=(
            "spectra.accepted_spectra",
            "search.accepted_psm",
            "inference.peptides",
            "inference.proteins",
            "qc.issues",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="import-spectra",
                description="parse MGF spectra and retain accepted blocks",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"mgf_text": mgf_text},
                output_payloads={"accepted_spectra": mgf_report.accepted_spectra},
                entity_counts={"accepted_spectra": len(spectra)},
                schema_names=("mgf_spectrum",),
            ),
            _step_artifact(
                step_id="map-psm",
                description="map normalized search hits to imported spectra",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "search_hits": search_hits,
                    "accepted_spectra": tuple(sorted(spectra)),
                },
                output_payloads={"accepted_psm": accepted_hits},
                entity_counts={"accepted_psm": len(accepted_hits)},
                schema_names=("dda_search_hit_input", "accepted_psm"),
                allowed_empty_reason=(
                    "imported spectra may fail to match any normalized search hit"
                ),
            ),
            _step_artifact(
                step_id="infer-peptide",
                description="aggregate accepted PSM rows into peptide evidence",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"accepted_psm": accepted_hits},
                output_payloads={"peptide_ids": peptides},
                entity_counts={"peptide_ids": len(peptides)},
                schema_names=("peptide_evidence",),
                allowed_empty_reason=(
                    "no peptide evidence can be inferred when no accepted PSM rows survive import"
                ),
            ),
            _step_artifact(
                step_id="infer-protein",
                description="aggregate peptide evidence into protein references",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"accepted_psm": accepted_hits, "peptide_ids": peptides},
                output_payloads={"protein_refs": proteins},
                entity_counts={"protein_refs": len(proteins)},
                schema_names=("protein_reference",),
                allowed_empty_reason=(
                    "no protein references can be inferred when no accepted peptide evidence remains"
                ),
            ),
            _step_artifact(
                step_id="qc-evidence",
                description="collect rejected spectra/hits into a QC issue surface",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "rejected_spectra": mgf_report.rejected_blocks,
                    "rejected_hits": rejected_hits,
                },
                output_payloads={
                    "qc_issues": {
                        "rejected_spectra": mgf_report.rejected_blocks,
                        "rejected_hits": rejected_hits,
                    }
                },
                entity_counts={"qc_issues": qc_issue_count},
                schema_names=("dda_qc_issue",),
                allowed_empty_reason=(
                    "all imported search hits may map cleanly to parsed spectra with no QC issues"
                ),
            ),
        ),
        note="workflow completed DDA import with mapped PSM, inferred peptide/protein evidence, and QC accounting",
    )


def run_dia_import_workflow_end_to_end(
    precursor_rows: tuple[DiaPrecursorQuantInput, ...],
    *,
    artifact_root: str = "artifacts/workflows/dia-import",
) -> DiaImportWorkflowRunReport:
    """Execute DIA runtime flow: import -> precursor/peptide/protein quant -> QC evidence."""
    precursors = tuple(sorted({row.precursor_id for row in precursor_rows}))
    peptides = tuple(sorted({row.peptide for row in precursor_rows}))
    proteins = tuple(sorted({row.protein_ref for row in precursor_rows}))
    quantified = tuple(row for row in precursor_rows if row.intensity is not None)
    missing = tuple(row for row in precursor_rows if row.intensity is None)
    key = _stable_runtime_key(
        {
            "workflow": "dia-import",
            "rows": [row.to_dict() for row in precursor_rows],
        }
    )
    return DiaImportWorkflowRunReport(
        workflow_id="dia-import",
        status=RuntimeWorkflowStatus.COMPLETED,
        precursor_count=len(precursors),
        peptide_count=len(peptides),
        protein_count=len(proteins),
        quantified_precursor_count=len({row.precursor_id for row in quantified}),
        qc_missing_intensity_count=len(missing),
        artifact_paths=(
            f"{artifact_root}/precursor_quant.tsv",
            f"{artifact_root}/peptide_quant.tsv",
            f"{artifact_root}/protein_quant.tsv",
            f"{artifact_root}/qc_report.json",
        ),
        evidence_pointers=(
            "dia.precursor_rows",
            "dia.peptide_quant",
            "dia.protein_quant",
            "dia.qc.missing_intensity_rows",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="import-dia-results",
                description="ingest DIA precursor-level quant rows",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"precursor_rows": precursor_rows},
                output_payloads={"precursor_rows": precursor_rows},
                entity_counts={"precursor_rows": len(precursor_rows)},
                schema_names=("dia_precursor_quant_input",),
            ),
            _step_artifact(
                step_id="aggregate-precursor",
                description="aggregate DIA rows at precursor level",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"precursor_rows": precursor_rows},
                output_payloads={"precursor_ids": precursors},
                entity_counts={"precursor_ids": len(precursors)},
                schema_names=("dia_precursor_quant_summary",),
            ),
            _step_artifact(
                step_id="aggregate-peptide",
                description="aggregate precursor evidence to peptide level",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"precursor_rows": precursor_rows},
                output_payloads={"peptide_ids": peptides},
                entity_counts={"peptide_ids": len(peptides)},
                schema_names=("dia_peptide_quant_summary",),
            ),
            _step_artifact(
                step_id="aggregate-protein",
                description="aggregate peptide evidence to protein level",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"peptide_ids": peptides, "precursor_rows": precursor_rows},
                output_payloads={"protein_refs": proteins},
                entity_counts={"protein_refs": len(proteins)},
                schema_names=("dia_protein_quant_summary",),
            ),
            _step_artifact(
                step_id="qc-evidence",
                description="collect DIA rows with missing intensities for QC review",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"precursor_rows": precursor_rows},
                output_payloads={"missing_intensity_rows": missing},
                entity_counts={"missing_intensity_rows": len(missing)},
                schema_names=("dia_missing_intensity_row",),
                allowed_empty_reason=(
                    "all DIA precursor rows may carry intensities with no missing-value QC pressure"
                ),
            ),
        ),
        note="workflow completed DIA import with precursor/peptide/protein quant and QC evidence",
    )


def run_quant_workflow_end_to_end(
    feature_records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    artifact_root: str = "artifacts/workflows/quant-runtime",
) -> QuantRuntimeWorkflowRunReport:
    """Execute quant runtime flow: matrix -> normalization -> DA -> review bundle."""
    review_bundle = build_quant_review_bundle(
        feature_records,
        design_entries=design_entries,
    )
    conditions = tuple(sorted({entry.condition for entry in design_entries}))
    key = _stable_runtime_key(
        {
            "workflow": "quant-runtime",
            "feature_count": len(feature_records),
            "design_count": len(design_entries),
            "condition_count": len(conditions),
            "bundle_hash": review_bundle.artifact_bundle_hash,
        }
    )
    outlier_count = len(review_bundle.qc_report.outlier_samples)
    return QuantRuntimeWorkflowRunReport(
        workflow_id="quant-runtime",
        status=RuntimeWorkflowStatus.COMPLETED,
        feature_record_count=len(feature_records),
        design_entry_count=len(design_entries),
        condition_count=len(conditions),
        outlier_sample_count=outlier_count,
        review_bundle_hash=review_bundle.artifact_bundle_hash or "missing",
        artifact_paths=(
            f"{artifact_root}/matrix.tsv",
            f"{artifact_root}/normalization.json",
            f"{artifact_root}/differential_abundance.tsv",
            f"{artifact_root}/review_bundle.json",
        ),
        evidence_pointers=(
            "quant.feature_records",
            "quant.normalization_matrix",
            "quant.effect_size_da_report",
            "quant.qc_report",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="build-matrix",
                description="build peptide-level quant matrix from features",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"feature_records": feature_records},
                output_payloads={"matrix_feature_records": feature_records},
                entity_counts={"matrix_feature_records": len(feature_records)},
                schema_names=("ms1_feature_record", "quant_matrix_surface"),
            ),
            _step_artifact(
                step_id="normalize",
                description="normalize quant matrix across samples",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "feature_records": feature_records,
                    "design_entries": design_entries,
                },
                output_payloads={
                    "normalized_conditions": conditions,
                    "outlier_samples": review_bundle.qc_report.outlier_samples,
                },
                entity_counts={"normalized_conditions": len(conditions)},
                schema_names=("experimental_design_entry", "normalized_condition_group"),
            ),
            _step_artifact(
                step_id="differential-abundance",
                description="compute effect-size-first differential abundance entries",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "feature_records": feature_records,
                    "design_entries": design_entries,
                    "condition_ids": conditions,
                },
                output_payloads={
                    "effect_size_entries": (
                        ()
                        if review_bundle.effect_size_da_report is None
                        else review_bundle.effect_size_da_report.entries
                    ),
                },
                entity_counts={
                    "effect_size_entries": (
                        len(review_bundle.effect_size_da_report.entries)
                        if review_bundle.effect_size_da_report is not None
                        else 0
                    )
                },
                schema_names=("effect_size_da_entry",),
                allowed_empty_reason=(
                    "the runtime review bundle may omit differential abundance entries when no analyte passes effect-size reporting thresholds"
                ),
            ),
            _step_artifact(
                step_id="review-bundle",
                description="assemble integrated quant review bundle",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "feature_records": feature_records,
                    "design_entries": design_entries,
                },
                output_payloads={
                    "review_bundle": review_bundle,
                    "artifact_paths": (
                        f"{artifact_root}/matrix.tsv",
                        f"{artifact_root}/normalization.json",
                        f"{artifact_root}/differential_abundance.tsv",
                        f"{artifact_root}/review_bundle.json",
                    ),
                },
                entity_counts={"evidence_pointers": len(review_bundle.evidence_pointers)},
                schema_names=("quant_review_bundle",),
            ),
        ),
        note="workflow completed quant matrix, normalization, differential abundance, and review bundle surfaces",
    )


def run_ptm_workflow_end_to_end(
    ptm_evidence_path: Path,
    *,
    protein_sequences: dict[str, str],
    feature_records: tuple[Ms1FeatureRecord, ...],
    artifact_root: str = "artifacts/workflows/ptm-runtime",
) -> PtmRuntimeWorkflowRunReport:
    """Execute PTM runtime flow: identification -> localization -> occupancy/motif -> packet."""
    parse_report = parse_ptm_localization_tsv(ptm_evidence_path)
    mappings = map_ptm_evidence_to_protein_sites(
        parse_report.accepted_records,
        protein_sequences=protein_sequences,
    )
    site_entries = build_ptm_site_table(mappings)
    occupancy = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=feature_records,
    )
    motifs = build_ptm_motif_windows(site_entries, protein_sequences=protein_sequences)
    lab_packet = build_ptm_lab_validation_packet(
        site_entries,
        occupancy_report=occupancy,
    )
    key = _stable_runtime_key(
        {
            "workflow": "ptm-runtime",
            "ptm_evidence_path": str(ptm_evidence_path),
            "accepted_identification_count": len(parse_report.accepted_records),
            "mapped_site_count": len(site_entries),
            "feature_count": len(feature_records),
        }
    )
    return PtmRuntimeWorkflowRunReport(
        workflow_id="ptm-runtime",
        status=RuntimeWorkflowStatus.COMPLETED,
        accepted_identification_count=len(parse_report.accepted_records),
        mapped_site_count=len(site_entries),
        motif_window_count=len(motifs),
        occupancy_entry_count=len(occupancy.entries),
        lab_packet_target_count=len(lab_packet.entries),
        unresolved_risk_count=lab_packet.unresolved_risk_count,
        artifact_paths=(
            f"{artifact_root}/ptm_sites.tsv",
            f"{artifact_root}/ptm_occupancy.tsv",
            f"{artifact_root}/ptm_motif_windows.tsv",
            f"{artifact_root}/ptm_lab_packet.json",
        ),
        evidence_pointers=(
            "ptm.accepted_identifications",
            "ptm.site_entries",
            "ptm.occupancy_entries",
            "ptm.lab_validation_packet",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="parse-identifications",
                description="parse PTM identification/localization evidence table",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"ptm_evidence_path": str(ptm_evidence_path)},
                output_payloads={"accepted_identifications": parse_report.accepted_records},
                entity_counts={
                    "accepted_identifications": len(parse_report.accepted_records)
                },
                schema_names=("ptm_localization_record",),
            ),
            _step_artifact(
                step_id="map-localization",
                description="map localized PTM evidence to protein site coordinates",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "accepted_identifications": parse_report.accepted_records,
                    "protein_sequences": protein_sequences,
                },
                output_payloads={"site_entries": site_entries},
                entity_counts={"site_entries": len(site_entries)},
                schema_names=("ptm_site_entry",),
                allowed_empty_reason=(
                    "localized PTM evidence may fail to map onto the supplied protein sequences"
                ),
            ),
            _step_artifact(
                step_id="estimate-occupancy",
                description="estimate modified/unmodified occupancy with counterpart caveats",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "site_entries": site_entries,
                    "feature_records": feature_records,
                },
                output_payloads={"occupancy_entries": occupancy.entries},
                entity_counts={"occupancy_entries": len(occupancy.entries)},
                schema_names=("ptm_occupancy_entry",),
                allowed_empty_reason=(
                    "occupancy estimation may remain empty when no mapped PTM site has a quantifiable counterpart"
                ),
            ),
            _step_artifact(
                step_id="build-motif",
                description="build PTM motif windows around mapped protein sites",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "site_entries": site_entries,
                    "protein_sequences": protein_sequences,
                },
                output_payloads={"motif_windows": motifs},
                entity_counts={"motif_windows": len(motifs)},
                schema_names=("ptm_motif_window",),
                allowed_empty_reason=(
                    "motif windows may remain empty when mapped PTM sites lack usable sequence context"
                ),
            ),
            _step_artifact(
                step_id="build-review-packet",
                description="build PTM lab validation packet with risk and controls",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "site_entries": site_entries,
                    "occupancy_entries": occupancy.entries,
                },
                output_payloads={"lab_validation_packet": lab_packet},
                entity_counts={"lab_validation_targets": len(lab_packet.entries)},
                schema_names=("ptm_lab_validation_packet",),
                allowed_empty_reason=(
                    "no PTM site may survive into the lab-validation packet when mapped evidence remains too weak for downstream assay planning"
                ),
            ),
        ),
        note="workflow completed PTM localization, occupancy, motif, and lab validation packet surfaces",
    )


def run_multiplex_workflow_end_to_end(
    feature_records: tuple[Ms1FeatureRecord, ...],
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    artifact_root: str = "artifacts/workflows/multiplex-runtime",
) -> MultiplexRuntimeWorkflowRunReport:
    """Execute multiplex runtime flow: channel policy -> diagnostics -> review bundle."""

    quant_table = build_label_free_intensity_table(
        feature_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    quant_policy = _build_label_policy(design_entries)
    diagnostics = build_multiplex_channel_balance_diagnostics_report(
        quant_table,
        design_entries=design_entries,
        quant_policy=quant_policy,
        normalization_policy=MultiplexNormalizationPolicy(),
    )
    bundle = build_label_based_quant_bundle(
        quant_table,
        design_entries=design_entries,
        policy=quant_policy,
    )
    review_bundle = build_quant_review_bundle(
        feature_records,
        design_entries=design_entries,
    )
    multiplex_groups = {
        entry.multiplex_group for entry in design_entries if entry.multiplex_group
    }
    reference_channel_count = sum(
        1
        for channel in bundle.channels
        if channel.channel_role is LabelBasedChannelRole.REFERENCE
    )
    key = _stable_runtime_key(
        {
            "workflow": "multiplex-runtime",
            "feature_count": len(feature_records),
            "channel_count": len(bundle.channels),
            "missing_channel_count": len(bundle.missing_channels),
            "flagged_imbalance_count": diagnostics.flagged_imbalance_count,
            "review_bundle_hash": review_bundle.artifact_bundle_hash,
        }
    )
    return MultiplexRuntimeWorkflowRunReport(
        workflow_id="multiplex-runtime",
        status=RuntimeWorkflowStatus.COMPLETED,
        feature_record_count=len(feature_records),
        multiplex_group_count=len(multiplex_groups),
        channel_count=len(bundle.channels),
        reference_channel_count=reference_channel_count,
        missing_channel_count=len(bundle.missing_channels),
        flagged_imbalance_count=diagnostics.flagged_imbalance_count,
        carrier_effect_channel_count=diagnostics.carrier_effect_channel_count,
        review_bundle_hash=review_bundle.artifact_bundle_hash or "missing",
        artifact_paths=(
            f"{artifact_root}/channel_matrix.tsv",
            f"{artifact_root}/channel_policy.json",
            f"{artifact_root}/interference_review.json",
            f"{artifact_root}/reference_channel_consequences.json",
            f"{artifact_root}/review_bundle.json",
        ),
        evidence_pointers=(
            "multiplex.feature_records",
            "multiplex.channel_policy",
            "multiplex.channel_balance_diagnostics",
            "multiplex.review_bundle",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="build-channel-matrix",
                description="build multiplex protein-level matrix from tracked feature records",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"feature_records": feature_records},
                output_payloads={"channel_matrix_features": feature_records},
                entity_counts={"channel_matrix_features": len(feature_records)},
                schema_names=("ms1_feature_record", "multiplex_channel_matrix"),
            ),
            _step_artifact(
                step_id="apply-channel-policy",
                description="apply explicit multiplex channel policy over tracked design entries",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "design_entries": design_entries,
                    "channel_policy": quant_policy,
                },
                output_payloads={"bundle_channels": bundle.channels},
                entity_counts={"bundle_channels": len(bundle.channels)},
                schema_names=("label_based_channel_policy_entry", "bundle_channel"),
            ),
            _step_artifact(
                step_id="review-channel-pressure",
                description="surface missing channels, carrier pressure, and flagged imbalance before biological rollup",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "channel_balance_diagnostics": diagnostics,
                    "quant_bundle": bundle,
                },
                output_payloads={
                    "channel_pressure": {
                        "flagged_imbalance_count": diagnostics.flagged_imbalance_count,
                        "missing_channel_count": diagnostics.missing_channel_count,
                        "carrier_effect_channel_count": diagnostics.carrier_effect_channel_count,
                    }
                },
                entity_counts={
                    "channel_pressure_events": (
                        diagnostics.flagged_imbalance_count
                        + diagnostics.missing_channel_count
                        + diagnostics.carrier_effect_channel_count
                    )
                },
                schema_names=("multiplex_channel_pressure_event",),
                allowed_empty_reason=(
                    "channel pressure can be absent when every multiplex channel passes missingness, imbalance, and carrier checks"
                ),
            ),
            _step_artifact(
                step_id="assemble-review-bundle",
                description="assemble multiplex review outputs with explicit downgrade pressure",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "feature_records": feature_records,
                    "design_entries": design_entries,
                },
                output_payloads={"review_bundle": review_bundle},
                entity_counts={"evidence_pointers": len(review_bundle.evidence_pointers)},
                schema_names=("quant_review_bundle", "multiplex_review_bundle"),
            ),
        ),
        note=(
            "workflow completed multiplex channel policy, interference-facing diagnostics, reference-channel consequences, and integrated review surfaces"
        ),
    )


def run_targeted_workflow_end_to_end(
    targeted_qc_path: Path,
    *,
    supported_follow_up_payload: dict[str, Any],
    failed_follow_up_payload: dict[str, Any],
    refused_follow_up_payload: dict[str, Any],
    artifact_root: str = "artifacts/workflows/targeted-runtime",
) -> TargetedRuntimeWorkflowRunReport:
    """Execute targeted runtime flow from QC to follow-up consequence surfaces."""

    qc_report = parse_chromatogram_qc_table(targeted_qc_path)
    approved_transition_count = _count_transition_ids(
        supported_follow_up_payload,
        "approved_transition_ids",
    )
    exploratory_transition_count = sum(
        _count_transition_ids(payload, "exploratory_transition_ids")
        for payload in (
            supported_follow_up_payload,
            failed_follow_up_payload,
            refused_follow_up_payload,
        )
    )
    refused_transition_count = sum(
        _count_transition_ids(payload, "refused_transition_ids")
        for payload in (
            supported_follow_up_payload,
            failed_follow_up_payload,
            refused_follow_up_payload,
        )
    )
    blocked_follow_up_count = sum(
        1
        for payload in (failed_follow_up_payload, refused_follow_up_payload)
        if isinstance(payload.get("workflow_readiness_summary"), dict)
    )
    observed_outcome_count = _count_assay_outcomes(supported_follow_up_payload)
    key = _stable_runtime_key(
        {
            "workflow": "targeted-runtime",
            "qc_path": str(targeted_qc_path),
            "qc_point_count": len(qc_report.accepted_points),
            "approved_transition_count": approved_transition_count,
            "exploratory_transition_count": exploratory_transition_count,
            "refused_transition_count": refused_transition_count,
            "blocked_follow_up_count": blocked_follow_up_count,
            "observed_outcome_count": observed_outcome_count,
        }
    )
    return TargetedRuntimeWorkflowRunReport(
        workflow_id="targeted-runtime",
        status=RuntimeWorkflowStatus.COMPLETED,
        qc_point_count=len(qc_report.accepted_points),
        approved_transition_count=approved_transition_count,
        exploratory_transition_count=exploratory_transition_count,
        refused_transition_count=refused_transition_count,
        blocked_follow_up_count=blocked_follow_up_count,
        observed_outcome_count=observed_outcome_count,
        artifact_paths=(
            f"{artifact_root}/chromatogram_qc.json",
            f"{artifact_root}/transition_review.json",
            f"{artifact_root}/calibration_readout.json",
            f"{artifact_root}/interference_review.json",
            f"{artifact_root}/follow_up_consequences.json",
        ),
        evidence_pointers=(
            "targeted.chromatogram_qc",
            "targeted.transition_review",
            "targeted.calibration_readout",
            "targeted.interference_review",
            "targeted.follow_up_consequences",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="ingest-chromatogram-qc",
                description="ingest targeted chromatogram QC rows as the calibration-facing runtime surface",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"targeted_qc_path": str(targeted_qc_path)},
                output_payloads={"accepted_points": qc_report.accepted_points},
                entity_counts={"accepted_points": len(qc_report.accepted_points)},
                schema_names=("chromatogram_qc_point",),
            ),
            _step_artifact(
                step_id="review-transitions",
                description="carry approved, exploratory, and refused transition states into runtime review",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "supported_follow_up_payload": supported_follow_up_payload,
                    "failed_follow_up_payload": failed_follow_up_payload,
                    "refused_follow_up_payload": refused_follow_up_payload,
                },
                output_payloads={
                    "transition_review": {
                        "approved_transition_count": approved_transition_count,
                        "exploratory_transition_count": exploratory_transition_count,
                        "refused_transition_count": refused_transition_count,
                    }
                },
                entity_counts={
                    "transition_review_entries": (
                        approved_transition_count
                        + exploratory_transition_count
                        + refused_transition_count
                    )
                },
                schema_names=("targeted_transition_review",),
                allowed_empty_reason=(
                    "follow-up payloads may not propose any approved, exploratory, or refused transitions"
                ),
            ),
            _step_artifact(
                step_id="surface-interference-pressure",
                description="keep blocked and refused targeted follow-up paths visible as interference-facing or readiness-facing pressure",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "failed_follow_up_payload": failed_follow_up_payload,
                    "refused_follow_up_payload": refused_follow_up_payload,
                },
                output_payloads={
                    "blocked_follow_up_paths": (
                        failed_follow_up_payload,
                        refused_follow_up_payload,
                    )
                },
                entity_counts={"blocked_follow_up_paths": blocked_follow_up_count},
                schema_names=("targeted_follow_up_pressure",),
                allowed_empty_reason=(
                    "targeted follow-up payloads may remain launchable without interference or readiness blockage"
                ),
            ),
            _step_artifact(
                step_id="publish-follow-up-consequences",
                description="publish the observed targeted follow-up outcomes that remain usable downstream",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"supported_follow_up_payload": supported_follow_up_payload},
                output_payloads={
                    "assay_outcomes": supported_follow_up_payload.get("outcome", {})
                },
                entity_counts={"assay_outcomes": observed_outcome_count},
                schema_names=("targeted_assay_outcome",),
                allowed_empty_reason=(
                    "supported targeted follow-up payloads may carry no observed assay outcomes yet"
                ),
            ),
        ),
        note=(
            "workflow completed targeted QC, transition review, calibration-facing traces, interference-facing pressure, and follow-up consequence surfaces"
        ),
    )


def run_knowledge_review_workflow_end_to_end(
    evidence_items: tuple[KnowledgeEvidenceInput, ...],
    *,
    artifact_root: str = "artifacts/workflows/knowledge-review",
) -> KnowledgeReviewWorkflowRunReport:
    """Execute evidence-graph -> trust -> ranking -> contradiction review workflow."""
    ranked = tuple(
        sorted(
            evidence_items,
            key=lambda item: (-item.trust_score, item.evidence_id),
        )
    )
    contradiction_pairs: set[tuple[str, str]] = set()
    evidence_map = {item.evidence_id: item for item in evidence_items}
    for item in evidence_items:
        for other_id in item.contradicts:
            if other_id in evidence_map:
                left_id, right_id = sorted((item.evidence_id, other_id))
                contradiction_pairs.add((left_id, right_id))
    contested = {evidence_id for pair in contradiction_pairs for evidence_id in pair}
    accepted = [
        item
        for item in ranked
        if item.evidence_id not in contested and item.trust_score >= 0.5
    ]
    key = _stable_runtime_key(
        {
            "workflow": "knowledge-review",
            "evidence": [item.to_dict() for item in evidence_items],
        }
    )
    return KnowledgeReviewWorkflowRunReport(
        workflow_id="knowledge-review",
        status=RuntimeWorkflowStatus.COMPLETED,
        evidence_node_count=len(evidence_items),
        ranked_evidence_count=len(ranked),
        contradiction_count=len(contradiction_pairs),
        accepted_claim_count=len(accepted),
        contested_claim_count=len(contested),
        artifact_paths=(
            f"{artifact_root}/evidence_graph.json",
            f"{artifact_root}/trust_ranking.tsv",
            f"{artifact_root}/contradiction_report.json",
            f"{artifact_root}/review_packet.json",
        ),
        evidence_pointers=(
            "knowledge.evidence_graph",
            "knowledge.trust_ranking",
            "knowledge.contradictions",
            "knowledge.review_packet",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="build-evidence-graph",
                description="build evidence graph from normalized evidence inputs",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"evidence_items": evidence_items},
                output_payloads={"evidence_nodes": evidence_items},
                entity_counts={"evidence_nodes": len(evidence_items)},
                schema_names=("knowledge_evidence_input", "knowledge_evidence_node"),
            ),
            _step_artifact(
                step_id="rank-trust",
                description="rank evidence entries by trust score",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"evidence_items": evidence_items},
                output_payloads={"ranked_evidence": ranked},
                entity_counts={"ranked_evidence": len(ranked)},
                schema_names=("ranked_evidence_entry",),
            ),
            _step_artifact(
                step_id="resolve-contradictions",
                description="flag contradictory evidence pairs for review",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"ranked_evidence": ranked},
                output_payloads={"contradiction_pairs": tuple(sorted(contradiction_pairs))},
                entity_counts={"contradiction_pairs": len(contradiction_pairs)},
                schema_names=("knowledge_contradiction_pair",),
                allowed_empty_reason=(
                    "normalized evidence inputs may contain no contradictory claims"
                ),
            ),
            _step_artifact(
                step_id="assemble-review-packet",
                description="assemble knowledge decision brief from ranked and contested claims",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "ranked_evidence": ranked,
                    "contradiction_pairs": tuple(sorted(contradiction_pairs)),
                },
                output_payloads={
                    "accepted_claims": accepted,
                    "contested_claim_ids": tuple(sorted(contested)),
                },
                entity_counts={"review_claims": len(accepted) + len(contested)},
                schema_names=("knowledge_review_claim",),
                allowed_empty_reason=(
                    "a knowledge review packet may remain empty when no evidence item clears the trust or contradiction screen"
                ),
            ),
        ),
        note="workflow completed evidence ranking and contradiction-aware knowledge decision brief generation",
    )


def run_lab_handoff_workflow_end_to_end(
    packet: _PtmLabValidationPacketLike,
    *,
    artifact_root: str = "artifacts/workflows/lab-handoff",
) -> LabHandoffWorkflowRunReport:
    """Execute lab handoff workflow from decision brief to export and unresolved-risk report."""
    planned_assays = sum(1 for entry in packet.entries if entry.target_peptides)
    unresolved = sum(
        1
        for entry in packet.entries
        if getattr(entry.assay_risk, "value", entry.assay_risk) in {"medium", "high"}
    )
    key = _stable_runtime_key(
        {
            "workflow": "lab-handoff",
            "entries": [entry.to_dict() for entry in packet.entries],
            "unresolved_risk_count": packet.unresolved_risk_count,
        }
    )
    return LabHandoffWorkflowRunReport(
        workflow_id="lab-handoff",
        status=RuntimeWorkflowStatus.COMPLETED,
        review_target_count=len(packet.entries),
        planned_assay_count=planned_assays,
        unresolved_risk_count=max(unresolved, packet.unresolved_risk_count),
        export_file_count=3,
        artifact_paths=(
            f"{artifact_root}/assay_plan.tsv",
            f"{artifact_root}/handoff_export.json",
            f"{artifact_root}/unresolved_risk_report.json",
        ),
        evidence_pointers=(
            "lab.review_packet",
            "lab.assay_plan",
            "lab.handoff_export",
            "lab.unresolved_risk_report",
        ),
        replay_cache_key=key,
        steps=(
            _step_artifact(
                step_id="ingest-review-packet",
                description="ingest PTM decision brief for assay planning",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"packet_entries": packet.entries},
                output_payloads={"review_targets": packet.entries},
                entity_counts={"review_targets": len(packet.entries)},
                schema_names=("ptm_lab_validation_target_entry",),
                allowed_empty_reason=(
                    "a lab handoff packet may carry no review targets when no PTM site survives validation screening"
                ),
            ),
            _step_artifact(
                step_id="build-assay-plan",
                description="build assay plan for target peptides and controls",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"packet_entries": packet.entries},
                output_payloads={"planned_assays": planned_assays},
                entity_counts={"planned_assays": planned_assays},
                schema_names=("planned_lab_assay",),
                allowed_empty_reason=(
                    "review targets may lack peptide coverage for immediate assay planning"
                ),
            ),
            _step_artifact(
                step_id="export-handoff",
                description="export lab handoff bundle for downstream execution",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={"packet_entries": packet.entries},
                output_payloads={
                    "export_paths": (
                        f"{artifact_root}/assay_plan.tsv",
                        f"{artifact_root}/handoff_export.json",
                        f"{artifact_root}/unresolved_risk_report.json",
                    )
                },
                entity_counts={"export_files": 3},
                schema_names=("lab_handoff_export_bundle",),
            ),
            _step_artifact(
                step_id="report-unresolved-risk",
                description="report unresolved assay risks that require scientific follow-up",
                status=RuntimeWorkflowStatus.COMPLETED,
                input_payloads={
                    "packet_entries": packet.entries,
                    "unresolved_risk_count": packet.unresolved_risk_count,
                },
                output_payloads={
                    "unresolved_risk_count": max(unresolved, packet.unresolved_risk_count)
                },
                entity_counts={
                    "unresolved_risk_entries": max(
                        unresolved, packet.unresolved_risk_count
                    )
                },
                schema_names=("lab_unresolved_risk_entry",),
                allowed_empty_reason=(
                    "every reviewed lab target may clear the unresolved-risk screen"
                ),
            ),
        ),
        note="workflow completed review-packet ingestion, assay planning, export, and unresolved-risk reporting",
    )


def build_simulated_external_engine_harness(
    *,
    run_id: str,
    tool_kinds: tuple[SimulatedExternalToolKind, ...] = (
        SimulatedExternalToolKind.SEARCH,
        SimulatedExternalToolKind.QUANT,
        SimulatedExternalToolKind.QC,
    ),
    seed: int = 17,
    artifact_root: str = "artifacts/workflows/simulated-external-engine-harness",
) -> SimulatedExternalEngineHarnessReport:
    """Run deterministic simulated search, quant, and QC surfaces for contract testing."""
    entries: list[SimulatedExternalToolRunEntry] = []
    for index, tool_kind in enumerate(tool_kinds):
        token = _stable_runtime_key(
            {
                "run_id": run_id,
                "tool_kind": tool_kind.value,
                "seed": seed,
                "index": index,
            }
        )[:16]
        entries.append(
            SimulatedExternalToolRunEntry(
                tool_kind=tool_kind,
                command=f"simulate-{tool_kind.value}-tool --seed {seed} --token {token}",
                exit_code=0,
                artifact_path=f"{artifact_root}/{tool_kind.value}-{token}.json",
                stdout=f"{tool_kind.value} simulation completed deterministically with token {token}",
            )
        )
    key = _stable_runtime_key(
        {
            "workflow": "simulated-external-engine-harness",
            "run_id": run_id,
            "seed": seed,
            "entries": [entry.to_dict() for entry in entries],
        }
    )
    return SimulatedExternalEngineHarnessReport(
        run_id=run_id,
        deterministic=True,
        entries=tuple(entries),
        replay_cache_key=key,
    )


def run_local_external_tool(
    *,
    command: tuple[str, ...],
    timeout_seconds: float = 30.0,
    env_overrides: dict[str, str] | None = None,
    expected_artifacts: tuple[str, ...] = (),
) -> LocalExternalToolRunReport:
    """Execute a configured local command with timeout, logs, and artifact validation."""
    if not command:
        raise ValueError("command must not be empty")
    env_overrides = env_overrides or {}
    binary = command[0]
    resolved = shutil.which(binary)
    if resolved is None:
        return LocalExternalToolRunReport(
            disposition=LocalExternalToolRunDisposition.REFUSED,
            command=command,
            timeout_seconds=timeout_seconds,
            env_overrides=env_overrides,
            note=f"refused to run because binary {binary!r} is not available on PATH",
        )
    env = dict(os.environ)
    env.update(env_overrides)
    try:
        completed = subprocess.run(  # nosec B603
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return LocalExternalToolRunReport(
            disposition=LocalExternalToolRunDisposition.TIMED_OUT,
            command=command,
            timeout_seconds=timeout_seconds,
            env_overrides=env_overrides,
            stdout=_normalize_stream(exc.stdout),
            stderr=_normalize_stream(exc.stderr),
            note="command timed out before completion",
        )
    validated = tuple(path for path in expected_artifacts if Path(path).exists())
    missing = tuple(path for path in expected_artifacts if not Path(path).exists())
    if completed.returncode == 0 and not missing:
        disposition = LocalExternalToolRunDisposition.COMPLETED
        note = "command completed and all expected artifacts were validated"
    elif completed.returncode == 0 and missing:
        disposition = LocalExternalToolRunDisposition.FAILED
        note = "command succeeded but one or more expected artifacts are missing"
    else:
        disposition = LocalExternalToolRunDisposition.FAILED
        note = "command failed with non-zero exit code"
    return LocalExternalToolRunReport(
        disposition=disposition,
        command=command,
        timeout_seconds=timeout_seconds,
        env_overrides=env_overrides,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        validated_artifacts=validated,
        missing_artifacts=missing,
        note=note,
    )


def build_proteomics_workflow_cache_replay_report(
    *,
    previous_artifact_hashes: dict[str, str],
    current_artifact_hashes: dict[str, str],
    reused_surfaces: tuple[str, ...] = (),
    refused_surfaces: tuple[str, ...] = (),
) -> WorkflowCacheReplayReport:
    """Classify cache/replay outcomes across repeated workflow runs."""
    surface_names = sorted(
        set(previous_artifact_hashes)
        | set(current_artifact_hashes)
        | set(reused_surfaces)
        | set(refused_surfaces)
    )
    entries: list[WorkflowCacheReplayEntry] = []
    for surface in surface_names:
        previous_hash = previous_artifact_hashes.get(surface)
        current_hash = current_artifact_hashes.get(surface)
        if surface in refused_surfaces:
            outcome = WorkflowReplayOutcome.REFUSED
            detail = "surface was refused during replay because execution constraints were not met"
        elif (
            surface in reused_surfaces
            and previous_hash == current_hash
            and current_hash is not None
        ):
            outcome = WorkflowReplayOutcome.REUSED
            detail = "surface reused cached output with stable content hash"
        elif previous_hash is None and current_hash is not None:
            outcome = WorkflowReplayOutcome.RERUN
            detail = "surface was produced in current run because no previous output hash existed"
        elif previous_hash is not None and current_hash is None:
            outcome = WorkflowReplayOutcome.REFUSED
            detail = (
                "surface is missing in current run and is treated as refused output"
            )
        elif previous_hash == current_hash:
            outcome = WorkflowReplayOutcome.UNCHANGED
            detail = "surface output remained unchanged across repeated runs"
        else:
            outcome = WorkflowReplayOutcome.CHANGED
            detail = "surface output hash changed across repeated runs"
        entries.append(
            WorkflowCacheReplayEntry(
                surface=surface,
                previous_hash=previous_hash,
                current_hash=current_hash,
                outcome=outcome,
                detail=detail,
            )
        )
    return WorkflowCacheReplayReport(
        entries=tuple(entries),
        reused_count=sum(
            1 for entry in entries if entry.outcome is WorkflowReplayOutcome.REUSED
        ),
        rerun_count=sum(
            1 for entry in entries if entry.outcome is WorkflowReplayOutcome.RERUN
        ),
        changed_count=sum(
            1 for entry in entries if entry.outcome is WorkflowReplayOutcome.CHANGED
        ),
        unchanged_count=sum(
            1 for entry in entries if entry.outcome is WorkflowReplayOutcome.UNCHANGED
        ),
        refused_count=sum(
            1 for entry in entries if entry.outcome is WorkflowReplayOutcome.REFUSED
        ),
    )
