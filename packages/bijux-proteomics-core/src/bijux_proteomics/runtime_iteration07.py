# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime end-to-end workflow execution surfaces for iteration 07."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json

from pydantic import ConfigDict, Field

from bijux_proteomics.digestion import digest_protein_records
from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    FastaParseMode,
    generate_decoy_records,
    parse_fasta_document,
)
from bijux_proteomics_foundation import JsonModel


class RuntimeWorkflowStatus(StrEnum):
    """Execution status for one runtime workflow report."""

    COMPLETED = "completed"
    REFUSED = "refused"
    FAILED = "failed"


class RuntimeWorkflowStepRecord(JsonModel):
    """One deterministic runtime step trace entry."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: RuntimeWorkflowStatus
    output_count: int = Field(..., ge=0)


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
    steps: tuple[RuntimeWorkflowStepRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _stable_runtime_key(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def run_sequence_to_digest_workflow_end_to_end(
    fasta_text: str,
    *,
    artifact_root: str = "artifacts/workflows/sequence-to-digest",
    decoy_mode: DecoyGenerationMode = DecoyGenerationMode.REVERSE,
) -> SequenceToDigestWorkflowRunReport:
    """Execute FASTA -> digest -> decoy -> peptide evidence end to end."""
    parse_report = parse_fasta_document(fasta_text, mode=FastaParseMode.STRICT)
    if not parse_report.accepted_records:
        key = _stable_runtime_key({"workflow": "sequence-to-digest", "fasta": fasta_text})
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
                RuntimeWorkflowStepRecord(
                    step_id="parse-fasta",
                    description="parse strict FASTA records",
                    status=RuntimeWorkflowStatus.REFUSED,
                    output_count=0,
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
            RuntimeWorkflowStepRecord(
                step_id="parse-fasta",
                description="parse strict FASTA records",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(targets),
            ),
            RuntimeWorkflowStepRecord(
                step_id="generate-decoys",
                description="generate deterministic decoy records",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(decoys),
            ),
            RuntimeWorkflowStepRecord(
                step_id="digest-targets",
                description="digest accepted target records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(target_peptides),
            ),
            RuntimeWorkflowStepRecord(
                step_id="digest-decoys",
                description="digest generated decoy records with trypsin",
                status=RuntimeWorkflowStatus.COMPLETED,
                output_count=len(decoy_peptides),
            ),
        ),
        note="workflow completed with deterministic FASTA, decoy, and digestion evidence surfaces",
    )
