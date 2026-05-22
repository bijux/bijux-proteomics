# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Search-result and peptide-spectrum match contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class TargetDecoyLabel(StrEnum):
    """Normalized target/decoy state for one evidence record."""

    TARGET = "target"
    DECOY = "decoy"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PsmSortField(StrEnum):
    """Supported stable PSM sorting policies."""

    SPECTRUM = "spectrum"
    SCORE = "score"
    Q_VALUE = "q_value"
    PEPTIDE = "peptide"


class SearchResultColumnMapping(JsonModel):
    """User-supplied mapping from engine columns to the stable PSM contract."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    intensity: str | None = None
    protein_refs: str | None = None
    q_value: str | None = None
    decoy_label: str | None = None
    contaminant_label: str | None = None
    protein_separator: str = ";"


class TargetDecoyLabelPolicy(JsonModel):
    """Policy for inferring target-decoy labels from search-result fields."""

    model_config = ConfigDict(extra="forbid")

    protein_prefix: str | None = "DECOY_"
    protein_suffix: str | None = None
    explicit_decoy_values: tuple[str, ...] = ("decoy", "true", "1")
    explicit_target_values: tuple[str, ...] = ("target", "false", "0")

    @field_validator("explicit_decoy_values", "explicit_target_values", mode="before")
    @classmethod
    def _normalize_values(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("decoy label values must be iterable")
            values = tuple(str(token) for token in value)
        return tuple(token.strip().lower() for token in values if token.strip())


class PsmRecord(JsonModel):
    """Stable peptide-spectrum match record."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    peptide_sequence: str | None = None
    modified_peptide: str | None = None
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    intensity: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    contaminant_flag: bool = False

    @field_validator(
        "run_id",
        "spectrum_id",
        "peptide",
        "peptide_sequence",
        "modified_peptide",
        "canonical_peptide",
        mode="before",
    )
    @classmethod
    def _strip_text_fields(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("spectrum_id", "peptide", "canonical_peptide")
    @classmethod
    def _require_text(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("field must not be blank")
        return value

    @field_validator("protein_refs", mode="before")
    @classmethod
    def _normalize_protein_refs(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            refs = [value]
        else:
            if not isinstance(value, Iterable):
                raise ValueError("protein references must be iterable")
            refs = [str(token) for token in value]
        normalized = tuple(token.strip() for token in refs if token.strip())
        return tuple(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def _derive_canonical_fields(self) -> PsmRecord:
        canonical_peptide, peptide_sequence, modified_peptide = (
            _derive_canonical_psm_peptide_fields(self.canonical_peptide)
        )

        if (
            self.peptide_sequence is not None
            and self.peptide_sequence.upper() != peptide_sequence
        ):
            raise ValueError(
                "peptide_sequence must match the residue sequence of canonical_peptide"
            )
        if self.modified_peptide is not None:
            _, _, provided_modified = _derive_canonical_psm_peptide_fields(
                self.modified_peptide
            )
            if provided_modified != modified_peptide:
                raise ValueError(
                    "modified_peptide must match canonical_peptide when both are provided"
                )

        self.run_id = self.run_id or None
        self.canonical_peptide = canonical_peptide
        self.peptide_sequence = peptide_sequence
        self.modified_peptide = modified_peptide
        if any(protein_ref.startswith("CON__") for protein_ref in self.protein_refs):
            self.contaminant_flag = True
        return self

    def to_domain_record(self) -> CanonicalPsmRecord:
        """Convert one identification-local PSM into the canonical domain record."""

        return CanonicalPsmRecord(
            run_id=self.run_id,
            spectrum_id=self.spectrum_id,
            peptide_sequence=self.peptide_sequence or self.peptide,
            canonical_peptide=self.canonical_peptide,
            charge_state=self.charge,
            score=self.score,
            modified_peptide=self.modified_peptide,
            intensity=self.intensity,
            q_value=self.q_value,
            protein_refs=self.protein_refs,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            contaminant_flag=self.contaminant_flag,
            metadata={"source_contract": "identification.psm_record"},
        )

    def to_modified_peptide_record(self) -> CanonicalModifiedPeptide:
        """Expose the modified-peptide view carried by one canonical PSM."""

        modified_peptide = self.modified_peptide or self.canonical_peptide
        parsed = parse_modified_peptide(modified_peptide)
        return CanonicalModifiedPeptide(
            record_id=self.spectrum_id,
            peptide_sequence=self.peptide_sequence or self.peptide,
            canonical_peptide=self.canonical_peptide,
            modified_peptide=modified_peptide,
            modification_names=tuple(
                dict.fromkeys(modification.name for modification in parsed.modifications)
            ),
            charge_state=self.charge,
            protein_refs=self.protein_refs,
            metadata={"source_contract": "identification.psm_record"},
        )


class SearchResultValidationIssue(JsonModel):
    """One validation issue while parsing or normalizing search results."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)


class RejectedPsmRow(JsonModel):
    """One rejected raw PSM row plus stable issue details."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_fields: dict[str, str] = Field(default_factory=dict)
    issues: tuple[SearchResultValidationIssue, ...] = Field(default_factory=tuple)

    def to_domain_record(self) -> CanonicalRejectedEvidence:
        """Expose one rejected PSM row as canonical rejected evidence."""

        issue_message = "; ".join(issue.message for issue in self.issues) or "rejected psm row"
        return CanonicalRejectedEvidence(
            record_kind="psm",
            rejection_reason=issue_message,
            row_number=self.row_number,
            raw_fields=self.raw_fields,
            metadata={
                "source_contract": "identification.rejected_psm_row",
                "issue_codes": ";".join(issue.code for issue in self.issues),
            },
        )


class PsmParseReport(JsonModel):
    """Result of parsing one generic PSM TSV file."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    column_mapping: SearchResultColumnMapping


class TargetDecoyCollisionEntry(JsonModel):
    """One target-decoy accession collision after base-accession normalization."""

    model_config = ConfigDict(extra="forbid")

    base_accession: str = Field(..., min_length=1)
    target_refs: tuple[str, ...] = Field(default_factory=tuple)
    decoy_refs: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)


class TargetDecoyCollisionReport(JsonModel):
    """Validation result for target-decoy accession collisions."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    collisions: tuple[TargetDecoyCollisionEntry, ...] = Field(default_factory=tuple)


class PeptideEvidenceEntry(JsonModel):
    """Rolled-up peptide-level evidence across PSMs."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    psm_count: int = Field(..., ge=1)
    spectrum_count: int = Field(..., ge=1)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    def to_domain_record(self) -> CanonicalPeptideRecord:
        """Convert one peptide evidence rollup into the canonical peptide record."""

        return CanonicalPeptideRecord(
            record_id=self.canonical_peptide,
            peptide_sequence=self.peptide,
            canonical_peptide=self.canonical_peptide,
            protein_refs=self.protein_refs,
            charge_states=self.charge_states,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={
                "source_contract": "identification.peptide_evidence",
                "psm_count": str(self.psm_count),
                "spectrum_count": str(self.spectrum_count),
            },
        )


class ProteinEvidenceEntry(JsonModel):
    """Rolled-up protein-level evidence across peptides and PSMs."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=1)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN

    def to_domain_record(self) -> CanonicalProteinRecord:
        """Convert one protein evidence rollup into the canonical protein record."""

        return CanonicalProteinRecord(
            record_id=self.protein_ref,
            primary_protein_ref=self.protein_ref,
            protein_refs=(self.protein_ref,),
            peptide_sequences=self.peptides,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={
                "source_contract": "identification.protein_evidence",
                "peptide_count": str(self.peptide_count),
                "unique_peptide_count": str(self.unique_peptide_count),
                "shared_peptide_count": str(self.shared_peptide_count),
                "spectrum_count": str(self.spectrum_count),
            },
        )


class FdrPolicy(JsonModel):
    """Stable policy for basic target-decoy FDR evaluation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better", pattern="^(higher_better|lower_better)$"
    )
    tie_handling: str = Field(
        default="score_group", pattern="^(score_group|stable_record_order)$"
    )
    threshold: float | None = Field(default=None, ge=0.0)
    decoy_policy: TargetDecoyLabelPolicy = Field(default_factory=TargetDecoyLabelPolicy)


class FdrAnnotatedPsm(JsonModel):
    """PSM record plus cumulative target-decoy FDR state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool = True


class NormalizedScoreEntry(JsonModel):
    """One PSM score normalized onto an orientation-stable rank scale."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class CalibrationPlotBin(JsonModel):
    """One score-calibration bin over normalized target-decoy evidence."""

    model_config = ConfigDict(extra="forbid")

    bin_lower: float = Field(..., ge=0.0, le=1.0)
    bin_upper: float = Field(..., ge=0.0, le=1.0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    decoy_fraction: float = Field(..., ge=0.0)


class CalibrationPlotData(JsonModel):
    """Plot-ready calibration data for one scored target-decoy ranking."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    total_psms: int = Field(..., ge=0)
    bins: tuple[CalibrationPlotBin, ...] = Field(default_factory=tuple)


class _CalibrationEvidenceRecord(JsonModel):
    """Internal scored evidence row for calibration across supported levels."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sort_token: str = Field(..., min_length=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class ScoreOrientationAdvisoryCandidate(JsonModel):
    """One candidate explanation for a score-orientation recommendation."""

    model_config = ConfigDict(extra="forbid")

    orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    top_ranked_count: int = Field(..., ge=0)
    top_target_count: int = Field(..., ge=0)
    top_decoy_count: int = Field(..., ge=0)
    top_mean_q_value: float | None = Field(default=None, ge=0.0)
    support_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class ScoreOrientationAdvisory(JsonModel):
    """Advisory recommendation over score orientation, never an enforced choice."""

    model_config = ConfigDict(extra="forbid")

    advisory_only: bool = True
    recommended_orientation: str | None = Field(
        default=None, pattern="^(higher_better|lower_better)$"
    )
    support_gap: float = Field(..., ge=0.0, le=1.0)
    candidates: tuple[ScoreOrientationAdvisoryCandidate, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FdrAuditEntry(JsonModel):
    """One sorted FDR-audit row with cumulative derivation state."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class FdrAuditTrail(JsonModel):
    """Stable audit payload for one target-decoy FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    policy: FdrPolicy
    entries: tuple[FdrAuditEntry, ...] = Field(default_factory=tuple)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


class FdrEvidenceLevel(StrEnum):
    """Supported evidence levels for level-specific FDR reporting."""

    PSM = "psm"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class FdrLevelEntry(JsonModel):
    """One FDR-annotated entity at the PSM, peptide, or protein level."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    member_count: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class LevelSpecificFdrReport(JsonModel):
    """Stable report over PSM-, peptide-, and protein-level FDR surfaces."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    psm_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    peptide_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)
    protein_entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class FdrQValueMonotonicityCheck(JsonModel):
    """One monotonicity verification result over an ordered FDR surface."""

    model_config = ConfigDict(extra="forbid")

    scope: str = Field(..., min_length=1)
    entry_count: int = Field(..., ge=0)
    valid: bool
    first_break_rank: int | None = Field(default=None, ge=1)


class FdrQValueMonotonicityReport(JsonModel):
    """Verification report for q-value monotonicity across supported FDR surfaces."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    checks: tuple[FdrQValueMonotonicityCheck, ...] = Field(default_factory=tuple)


class FdrEdgeCaseKind(StrEnum):
    """Explicit edge-case classification for target-decoy result sets."""

    MIXED = "mixed"
    ALL_TARGET = "all_target"
    ALL_DECOY = "all_decoy"
    NO_DECOY = "no_decoy"
    EMPTY = "empty"


class FdrEdgeCaseReport(JsonModel):
    """Structured report for notable target-decoy edge cases."""

    model_config = ConfigDict(extra="forbid")

    kind: FdrEdgeCaseKind
    total_records: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class GroupedFdrBucket(JsonModel):
    """One grouped-FDR bucket with its own ranked entries."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class GroupedFdrReport(JsonModel):
    """Stable grouped-FDR report across multiple evidence buckets."""

    model_config = ConfigDict(extra="forbid")

    group_by: str = Field(..., pattern="^(charge_state|modification_state)$")
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    groups: tuple[GroupedFdrBucket, ...] = Field(default_factory=tuple)


class SharedPeptideAmbiguityReason(StrEnum):
    """Reason a protein group remains ambiguous."""

    INDISTINGUISHABLE_MEMBERS = "indistinguishable_members"
    EXTERNAL_SHARED_PEPTIDES = "external_shared_peptides"
    MIXED = "mixed"


class ProteinGroupEntry(JsonModel):
    """One indistinguishable protein group from shared peptide evidence."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel

    def to_domain_record(self) -> CanonicalProteinGroup:
        """Convert one identification-local protein group into the canonical record."""

        return CanonicalProteinGroup(
            group_id=self.group_id,
            representative_protein=self.representative_protein,
            protein_refs=self.protein_refs,
            peptides=self.peptides,
            unique_peptide_count=self.unique_peptide_count,
            shared_peptide_count=self.shared_peptide_count,
            score=self.best_score,
            q_value=self.best_q_value,
            target_decoy_state=TargetDecoyState(self.target_decoy_label.value),
            metadata={"source_contract": "identification.protein_group"},
        )


class SharedPeptideAmbiguityEntry(JsonModel):
    """Explanation for why a protein group remains ambiguous."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    unique_peptides: tuple[str, ...] = Field(default_factory=tuple)
    outside_group_proteins: tuple[str, ...] = Field(default_factory=tuple)
    reason: SharedPeptideAmbiguityReason
    explanation: str = Field(..., min_length=1)


class SharedPeptideAmbiguityReport(JsonModel):
    """Ambiguity explanations over the protein groups implied by peptide sharing."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[SharedPeptideAmbiguityEntry, ...] = Field(default_factory=tuple)


class ParsimonyVariant(StrEnum):
    """Named protein-parsimony policies supported by core inference."""

    GREEDY_COVERAGE = "greedy_coverage"
    UNIQUE_EVIDENCE_PRIORITY = "unique_evidence_priority"
    BEST_SCORE_PRIORITY = "best_score_priority"


class ParsimonyProteinEntry(JsonModel):
    """One protein selected by the greedy parsimony inference policy."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    selection_rank: int = Field(..., ge=1)
    protein_ref: str = Field(..., min_length=1)
    source_group_id: str = Field(..., min_length=1)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_explained_peptides: tuple[str, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class RazorPeptideAssignment(JsonModel):
    """One peptide-to-protein assignment under a razor policy."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    assigned_protein: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class RazorPeptideProvenanceEntry(JsonModel):
    """Audit-friendly evidence for one razor peptide assignment."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    candidate_proteins: tuple[str, ...] = Field(default_factory=tuple)
    assigned_protein: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    candidate_unique_peptide_counts: dict[str, int] = Field(default_factory=dict)
    candidate_best_scores: dict[str, float] = Field(default_factory=dict)


class RazorPeptideProvenanceReport(JsonModel):
    """Razor assignment policy plus per-peptide audit evidence."""

    model_config = ConfigDict(extra="forbid")

    policy_name: str = Field(..., min_length=1)
    tie_break_order: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[RazorPeptideProvenanceEntry, ...] = Field(default_factory=tuple)


class CombinedEvidenceQuantSupport(JsonModel):
    """Quant support for one protein/sample slice inside a combined evidence view."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)


class CombinedEvidenceEntry(JsonModel):
    """Joined PSM, peptide, protein, PTM, and quant evidence for review."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    psm_count: int = Field(..., ge=0)
    best_psm_q_value: float | None = Field(default=None, ge=0.0)
    peptide_charge_states: tuple[int, ...] = Field(default_factory=tuple)
    protein_group_id: str | None = None
    protein_group_members: tuple[str, ...] = Field(default_factory=tuple)
    parsimony_variants: tuple[ParsimonyVariant, ...] = Field(default_factory=tuple)
    ptm_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    quant_support: tuple[CombinedEvidenceQuantSupport, ...] = Field(
        default_factory=tuple
    )


class CombinedEvidenceReport(JsonModel):
    """Stable combined evidence view across identification-adjacent surfaces."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CombinedEvidenceEntry, ...] = Field(default_factory=tuple)


class PeptideProteinTraceEntry(JsonModel):
    """Stable peptide-to-protein trace row for downstream review and export."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    spectrum_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    protein_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    charge_states: tuple[int, ...] = Field(default_factory=tuple)
    best_score: float
    best_q_value: float | None = Field(default=None, ge=0.0)


class PeptideProteinTraceReport(JsonModel):
    """Stable peptide-to-protein trace collection."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PeptideProteinTraceEntry, ...] = Field(default_factory=tuple)


class InferenceDisagreementKind(StrEnum):
    """Kinds of inference disagreements surfaced for review."""

    PEPTIDE_ASSIGNMENT = "peptide_assignment"
    PROTEIN_SET = "protein_set"


class InferenceDisagreementEntry(JsonModel):
    """One explicit disagreement between inference strategies."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(..., min_length=1)
    kind: InferenceDisagreementKind
    strategy_assignments: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)


class InferenceDisagreementReport(JsonModel):
    """Review-oriented report of disagreements between inference strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[InferenceDisagreementEntry, ...] = Field(default_factory=tuple)


class ParsimonyVariantResult(JsonModel):
    """Selections produced by one named protein-parsimony policy."""

    model_config = ConfigDict(extra="forbid")

    variant: ParsimonyVariant
    selected_proteins: tuple[ParsimonyProteinEntry, ...] = Field(default_factory=tuple)


class ParsimonyVariantDifferenceEntry(JsonModel):
    """Difference summary between two named parsimony policies."""

    model_config = ConfigDict(extra="forbid")

    left_variant: ParsimonyVariant
    right_variant: ParsimonyVariant
    first_difference_rank: int | None = Field(default=None, ge=1)
    shared_selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    left_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    right_only_proteins: tuple[str, ...] = Field(default_factory=tuple)


class ParsimonyVariantComparisonReport(JsonModel):
    """Comparison across multiple named parsimony policies."""

    model_config = ConfigDict(extra="forbid")

    results: tuple[ParsimonyVariantResult, ...] = Field(default_factory=tuple)
    differences: tuple[ParsimonyVariantDifferenceEntry, ...] = Field(
        default_factory=tuple
    )


class ProteinCoverageEntry(JsonModel):
    """Sequence-aware protein coverage summary from identified peptides."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    residue_count: int = Field(..., ge=1)
    covered_residue_count: int = Field(..., ge=0)
    coverage_fraction: float = Field(..., ge=0.0, le=1.0)
    covered_ranges: tuple[tuple[int, int], ...] = Field(default_factory=tuple)
    covered_peptides: tuple[str, ...] = Field(default_factory=tuple)


class DatabasePeptideUniqueness(StrEnum):
    """Uniqueness classification across a provided protein database."""

    UNIQUE = "unique"
    SHARED = "shared"
    MISSING = "missing"


class DatabasePeptideUniquenessEntry(JsonModel):
    """One peptide uniqueness entry over a provided database."""

    model_config = ConfigDict(extra="forbid")

    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    uniqueness: DatabasePeptideUniqueness


class PickedProteinFdrEntry(JsonModel):
    """One picked target-decoy protein entry with FDR state."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    partner_ref: str | None = None
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    supporting_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ConfidenceLabel(StrEnum):
    """Stable confidence labels over q-valued evidence."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"
    DECOY = "decoy"


class ConfidenceAssignment(JsonModel):
    """Confidence label plus its explanation."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0)
    label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class ConfidenceCalibrationLevel(StrEnum):
    """Evidence levels supported by the calibration assessment surface."""

    PSM = "psm"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class ConfidenceCalibrationEntry(JsonModel):
    """Calibration-aware confidence summary beyond raw q-values."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: ConfidenceCalibrationLevel
    entity_id: str = Field(..., min_length=1)
    q_value: float | None = Field(default=None, ge=0.0)
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    calibration_bin_lower: float = Field(..., ge=0.0, le=1.0)
    calibration_bin_upper: float = Field(..., ge=0.0, le=1.0)
    empirical_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    support_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class ConfidenceCalibrationReport(JsonModel):
    """Calibration assessment that keeps empirical decoy context beside q-values."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: ConfidenceCalibrationLevel
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    entries: tuple[ConfidenceCalibrationEntry, ...] = Field(default_factory=tuple)
    calibration_plot: CalibrationPlotData


class LevelSpecificConfidenceAssignment(JsonModel):
    """Confidence assignment for one explicit evidence level."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0)
    label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class LevelSpecificConfidenceReport(JsonModel):
    """Separate confidence assignments for PSM, peptide, and protein levels."""

    model_config = ConfigDict(extra="forbid")

    psm_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )
    peptide_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )
    protein_assignments: tuple[LevelSpecificConfidenceAssignment, ...] = Field(
        default_factory=tuple
    )


class ConfidenceThresholdSensitivityEntry(JsonModel):
    """Accepted-entity changes at one explicit confidence threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0, le=1.0)
    accepted_psm_count: int = Field(..., ge=0)
    accepted_peptide_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    accepted_picked_protein_count: int = Field(..., ge=0)
    newly_accepted_psm_ids: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_peptides: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_proteins: tuple[str, ...] = Field(default_factory=tuple)
    newly_accepted_picked_proteins: tuple[str, ...] = Field(default_factory=tuple)


class ConfidenceThresholdSensitivityReport(JsonModel):
    """Sensitivity report over explicit FDR acceptance thresholds."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    entries: tuple[ConfidenceThresholdSensitivityEntry, ...] = Field(
        default_factory=tuple
    )


class AcceptedPsmProvenanceEntry(JsonModel):
    """Full accepted-PSM provenance row after target-decoy thresholding."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    score_transform: str = Field(..., min_length=1)


class AcceptedPsmProvenanceReport(JsonModel):
    """Accepted PSMs plus the exact policy context that retained them."""

    model_config = ConfigDict(extra="forbid")

    threshold: float | None = Field(default=None, ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    tie_handling: str = Field(..., pattern="^(score_group|stable_record_order)$")
    score_transform: str = Field(..., min_length=1)
    entries: tuple[AcceptedPsmProvenanceEntry, ...] = Field(default_factory=tuple)


class PsmSummaryReport(JsonModel):
    """Compact search-result summary over normalized PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_psms: int = Field(..., ge=0)
    target_psms: int = Field(..., ge=0)
    decoy_psms: int = Field(..., ge=0)
    mixed_psms: int = Field(..., ge=0)
    unknown_psms: int = Field(..., ge=0)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    counts_by_score_bin: dict[str, int] = Field(default_factory=dict)


class PeptideSummaryReport(JsonModel):
    """Compact peptide-level summary derived from PSM records."""

    model_config = ConfigDict(extra="forbid")

    total_peptides: int = Field(..., ge=0)
    modified_peptides: int = Field(..., ge=0)
    unique_peptides: int = Field(..., ge=0)
    shared_peptides: int = Field(..., ge=0)
    decoy_peptides: int = Field(..., ge=0)


class ProteinSummaryEntry(JsonModel):
    """One protein summary row with optional sequence coverage."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)


class ProteinSummaryReport(JsonModel):
    """Compact protein-level summary over evidence rollups."""

    model_config = ConfigDict(extra="forbid")

    total_proteins: int = Field(..., ge=0)
    target_proteins: int = Field(..., ge=0)
    decoy_proteins: int = Field(..., ge=0)
    protein_groups: tuple[ProteinSummaryEntry, ...] = Field(default_factory=tuple)


class GroupedConfidenceEntry(JsonModel):
    """Confidence summary for one indistinguishable protein group."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    representative_protein: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    best_q_value: float | None = Field(default=None, ge=0.0)
    confidence_label: ConfidenceLabel
    explanation: str = Field(..., min_length=1)


class GroupedConfidenceReport(JsonModel):
    """Grouped confidence view over protein families and indistinguishable groups."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[GroupedConfidenceEntry, ...] = Field(default_factory=tuple)


class SearchResultProvenanceManifest(JsonModel):
    """Stable manifest for one search-result parsing and filtering operation."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str | None = None
    source_sha256: str | None = None
    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    column_mapping: SearchResultColumnMapping
    decoy_policy: TargetDecoyLabelPolicy
    fdr_policy: FdrPolicy | None = None


class DecoyStrategyValidationIssue(JsonModel):
    """One validation issue for a custom target-decoy strategy."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")


class DecoyStrategyValidationReport(JsonModel):
    """Validation result for a target-decoy labeling strategy."""

    model_config = ConfigDict(extra="forbid")

    policy: TargetDecoyLabelPolicy
    valid: bool
    issues: tuple[DecoyStrategyValidationIssue, ...] = Field(default_factory=tuple)


class ReviewReadyEvidenceBundle(JsonModel):
    """Production-ready evidence bundle for downstream scientific review."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    threshold: float = Field(..., ge=0.0)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    psm_summary: PsmSummaryReport
    peptide_summary: PeptideSummaryReport
    protein_summary: ProteinSummaryReport
    accepted_psm_provenance: AcceptedPsmProvenanceReport
    grouped_confidence: GroupedConfidenceReport
    combined_evidence: CombinedEvidenceReport
    peptide_traces: PeptideProteinTraceReport


class PtmIdentificationObservation(JsonModel):
    """Minimal PTM localization evidence needed for identification confidence checks."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    localization_score: float = Field(..., ge=0.0, le=1.0)
    candidate_site_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class PtmIdentificationConfidenceIssue(JsonModel):
    """One validation issue for PTM-specific identification confidence."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")


class PtmIdentificationConfidenceEntry(JsonModel):
    """PTM evidence row plus site-confidence validation outcome."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    valid: bool
    issues: tuple[PtmIdentificationConfidenceIssue, ...] = Field(default_factory=tuple)


class PtmIdentificationConfidenceReport(JsonModel):
    """Validation summary for PTM-specific identification confidence claims."""

    model_config = ConfigDict(extra="forbid")

    q_value_threshold: float = Field(..., ge=0.0, le=1.0)
    min_localization_score: float = Field(..., ge=0.0, le=1.0)
    entries: tuple[PtmIdentificationConfidenceEntry, ...] = Field(default_factory=tuple)


def _parse_protein_refs(raw_value: str | None, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    text = raw_value.strip() if raw_value is not None else ""
    refs = tuple(token.strip() for token in text.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _parse_contaminant_label(raw_value: str | None) -> bool | None:
    if raw_value is None:
        return None
    token = raw_value.strip().lower()
    if not token:
        return None
    if token in {"contaminant", "true", "1", "yes"}:
        return True
    if token in {"target", "false", "0", "no", "clean", "noncontaminant"}:
        return False
    raise ValueError("invalid contaminant label")


def _derive_canonical_psm_peptide_fields(
    peptide: str,
) -> tuple[str, str, str | None]:
    canonical_peptide = canonicalize_modified_peptide(peptide)
    if "[" not in canonical_peptide and "-[" not in canonical_peptide:
        return canonical_peptide, canonical_peptide, None
    parsed = parse_modified_peptide(canonical_peptide)
    return parsed.canonical_notation, parsed.sequence, parsed.canonical_notation


def _rank_label(label: TargetDecoyLabel) -> int:
    if label is TargetDecoyLabel.DECOY:
        return 3
    if label is TargetDecoyLabel.MIXED:
        return 2
    if label is TargetDecoyLabel.TARGET:
        return 1
    return 0


def _combine_labels(labels: tuple[TargetDecoyLabel, ...]) -> TargetDecoyLabel:
    active = tuple(label for label in labels if label is not TargetDecoyLabel.UNKNOWN)
    if not active:
        return TargetDecoyLabel.UNKNOWN
    if all(label is TargetDecoyLabel.DECOY for label in active):
        return TargetDecoyLabel.DECOY
    if all(label is TargetDecoyLabel.TARGET for label in active):
        return TargetDecoyLabel.TARGET
    if any(label is TargetDecoyLabel.MIXED for label in active):
        return TargetDecoyLabel.MIXED
    return TargetDecoyLabel.MIXED


def validate_target_decoy_policy(
    policy: TargetDecoyLabelPolicy,
    *,
    sample_protein_refs: tuple[str, ...] = (),
    sample_explicit_labels: tuple[str, ...] = (),
) -> DecoyStrategyValidationReport:
    """Validate a custom target-decoy strategy before downstream inference."""
    issues: list[DecoyStrategyValidationIssue] = []
    overlap = set(policy.explicit_decoy_values) & set(policy.explicit_target_values)
    if overlap:
        issues.append(
            DecoyStrategyValidationIssue(
                code="overlapping_explicit_values",
                message=(
                    "explicit target and decoy labels overlap: "
                    + ", ".join(sorted(overlap))
                ),
                severity="error",
            )
        )
    if not (
        policy.protein_prefix
        or policy.protein_suffix
        or policy.explicit_decoy_values
        or policy.explicit_target_values
    ):
        issues.append(
            DecoyStrategyValidationIssue(
                code="missing_decoy_rules",
                message="target-decoy policy does not define any explicit labels or protein naming rules",
                severity="error",
            )
        )
    unknown_labels = tuple(
        sorted(
            {
                label.strip().lower()
                for label in sample_explicit_labels
                if label.strip()
                and label.strip().lower() not in policy.explicit_decoy_values
                and label.strip().lower() not in policy.explicit_target_values
            }
        )
    )
    if unknown_labels:
        issues.append(
            DecoyStrategyValidationIssue(
                code="unmapped_explicit_labels",
                message=(
                    "explicit labels are present in sample evidence but absent from the custom policy: "
                    + ", ".join(unknown_labels)
                ),
                severity="warning",
            )
        )
    target_like = {
        protein_ref
        for protein_ref in sample_protein_refs
        if parse_target_decoy_label(protein_refs=(protein_ref,), policy=policy)
        is TargetDecoyLabel.TARGET
    }
    decoy_like = {
        protein_ref
        for protein_ref in sample_protein_refs
        if parse_target_decoy_label(protein_refs=(protein_ref,), policy=policy)
        is TargetDecoyLabel.DECOY
    }
    if sample_protein_refs and not decoy_like:
        issues.append(
            DecoyStrategyValidationIssue(
                code="sample_missing_decoy_matches",
                message="sample protein references do not contain any accessions recognized as decoy by the custom policy",
                severity="warning",
            )
        )
    if (
        target_like
        and decoy_like
        and any(
            _base_accession_from_policy(target_ref, policy)
            == _base_accession_from_policy(decoy_ref, policy)
            for target_ref in target_like
            for decoy_ref in decoy_like
        )
    ):
        issues.append(
            DecoyStrategyValidationIssue(
                code="shared_base_accession_pairs",
                message="sample evidence contains target and decoy accessions that collapse to the same base accession under the custom policy",
                severity="warning",
            )
        )
    return DecoyStrategyValidationReport(
        policy=policy,
        valid=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def validate_ptm_identification_confidence(
    observations: tuple[PtmIdentificationObservation, ...],
    *,
    q_value_threshold: float = 0.05,
    min_localization_score: float = 0.75,
) -> PtmIdentificationConfidenceReport:
    """Validate whether PTM-specific identifications are strong enough for review."""
    entries: list[PtmIdentificationConfidenceEntry] = []
    for observation in observations:
        issues: list[PtmIdentificationConfidenceIssue] = []
        if observation.target_decoy_label is TargetDecoyLabel.DECOY:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="decoy_ptm_evidence",
                    message="decoy PTM evidence cannot support a biological site claim",
                    severity="error",
                )
            )
        if observation.q_value > q_value_threshold:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="q_value_above_threshold",
                    message=(
                        f"q-value {observation.q_value:.4f} exceeds the PTM identification threshold"
                    ),
                    severity="error",
                )
            )
        if observation.localization_score < min_localization_score:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="weak_localization_score",
                    message=(
                        "PTM localization score is below the minimum site-confidence threshold"
                    ),
                    severity="warning",
                )
            )
        if observation.candidate_site_count > 1:
            issues.append(
                PtmIdentificationConfidenceIssue(
                    code="ambiguous_site_localization",
                    message="multiple candidate PTM sites remain plausible for this identification",
                    severity="warning",
                )
            )
        entries.append(
            PtmIdentificationConfidenceEntry(
                spectrum_id=observation.spectrum_id,
                canonical_peptide=observation.canonical_peptide,
                valid=not any(issue.severity == "error" for issue in issues),
                issues=tuple(issues),
            )
        )
    return PtmIdentificationConfidenceReport(
        q_value_threshold=q_value_threshold,
        min_localization_score=min_localization_score,
        entries=tuple(entries),
    )


def parse_target_decoy_label(
    *,
    protein_refs: tuple[str, ...] = (),
    explicit_label: str | None = None,
    policy: TargetDecoyLabelPolicy | None = None,
) -> TargetDecoyLabel:
    """Parse target-decoy state from explicit and protein-reference signals."""
    active_policy = policy or TargetDecoyLabelPolicy()
    if explicit_label is not None and explicit_label.strip():
        normalized = explicit_label.strip().lower()
        if normalized in active_policy.explicit_decoy_values:
            return TargetDecoyLabel.DECOY
        if normalized in active_policy.explicit_target_values:
            return TargetDecoyLabel.TARGET

    if not protein_refs:
        return TargetDecoyLabel.UNKNOWN

    prefix = active_policy.protein_prefix or ""
    suffix = active_policy.protein_suffix or ""
    labels: list[TargetDecoyLabel] = []
    for protein_ref in protein_refs:
        is_prefix = bool(prefix) and protein_ref.startswith(prefix)
        is_suffix = bool(suffix) and protein_ref.endswith(suffix)
        labels.append(
            TargetDecoyLabel.DECOY
            if is_prefix or is_suffix
            else TargetDecoyLabel.TARGET
        )
    return _combine_labels(tuple(labels))


def _base_accession_from_policy(
    protein_ref: str,
    policy: TargetDecoyLabelPolicy,
) -> str:
    value = protein_ref
    if policy.protein_prefix and value.startswith(policy.protein_prefix):
        value = value[len(policy.protein_prefix) :]
    if policy.protein_suffix and value.endswith(policy.protein_suffix):
        value = value[: -len(policy.protein_suffix)]
    return value


def validate_target_decoy_accession_collisions(
    records: tuple[PsmRecord, ...],
    *,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> TargetDecoyCollisionReport:
    """Detect target-decoy accession collisions before confidence scoring."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    collisions: list[TargetDecoyCollisionEntry] = []
    for record in records:
        grouped: dict[str, dict[str, set[str]]] = defaultdict(
            lambda: {"target_refs": set(), "decoy_refs": set()}
        )
        for protein_ref in record.protein_refs:
            bucket = grouped[_base_accession_from_policy(protein_ref, active_policy)]
            label = parse_target_decoy_label(
                protein_refs=(protein_ref,),
                policy=active_policy,
            )
            if label is TargetDecoyLabel.DECOY:
                bucket["decoy_refs"].add(protein_ref)
            else:
                bucket["target_refs"].add(protein_ref)
        for base_accession, bucket in sorted(grouped.items()):
            if bucket["target_refs"] and bucket["decoy_refs"]:
                collisions.append(
                    TargetDecoyCollisionEntry(
                        base_accession=base_accession,
                        target_refs=tuple(sorted(bucket["target_refs"])),
                        decoy_refs=tuple(sorted(bucket["decoy_refs"])),
                        spectrum_ids=(record.spectrum_id,),
                    )
                )
    return TargetDecoyCollisionReport(
        valid=not collisions,
        collisions=tuple(collisions),
    )


def _raise_on_target_decoy_accession_collisions(
    records: tuple[PsmRecord, ...],
    *,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> None:
    report = validate_target_decoy_accession_collisions(
        records,
        decoy_policy=decoy_policy,
    )
    if report.valid:
        return
    collision = report.collisions[0]
    raise ValueError(
        "target-decoy accession collision detected for "
        f"{collision.base_accession!r}: targets={','.join(collision.target_refs)} "
        f"decoys={','.join(collision.decoy_refs)}"
    )


def _row_issue(code: str, message: str, row_number: int) -> SearchResultValidationIssue:
    return SearchResultValidationIssue(
        code=code, message=message, row_number=row_number
    )


def _parse_psm_row(
    row: dict[str, str],
    *,
    row_number: int,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy,
) -> PsmRecord:
    issues: list[SearchResultValidationIssue] = []

    run_id = None
    if mapping.run_id:
        run_id = row.get(mapping.run_id, "").strip() or None

    spectrum_id = row.get(mapping.spectrum_id, "").strip()
    if not spectrum_id:
        issues.append(
            _row_issue("missing_spectrum_id", "missing spectrum identifier", row_number)
        )

    peptide = row.get(mapping.peptide, "").strip()
    if not peptide:
        issues.append(
            _row_issue("missing_peptide", "missing peptide sequence", row_number)
        )

    modified_peptide_token = None
    if mapping.modified_peptide:
        modified_peptide_token = row.get(mapping.modified_peptide, "").strip() or None

    try:
        charge = int(row.get(mapping.charge, "").strip())
        if charge < 1:
            raise ValueError
    except ValueError:
        issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))
        charge = 0

    try:
        score = float(row.get(mapping.score, "").strip())
    except ValueError:
        issues.append(_row_issue("invalid_score", "invalid score value", row_number))
        score = 0.0

    intensity: float | None = None
    if mapping.intensity:
        intensity_token = row.get(mapping.intensity, "").strip()
        if intensity_token:
            try:
                intensity = float(intensity_token)
                if intensity < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )

    q_value: float | None = None
    if mapping.q_value:
        q_token = row.get(mapping.q_value, "").strip()
        if q_token:
            try:
                q_value = float(q_token)
                if q_value < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue("invalid_q_value", "invalid q-value", row_number)
                )

    protein_refs = _parse_protein_refs(
        row.get(mapping.protein_refs) if mapping.protein_refs else None,
        mapping.protein_separator,
    )
    explicit_label = row.get(mapping.decoy_label) if mapping.decoy_label else None
    contaminant_flag = any(
        protein_ref.startswith("CON__") for protein_ref in protein_refs
    )
    if mapping.contaminant_label:
        try:
            explicit_contaminant = _parse_contaminant_label(
                row.get(mapping.contaminant_label)
            )
        except ValueError:
            issues.append(
                _row_issue(
                    "invalid_contaminant_label",
                    "invalid contaminant label",
                    row_number,
                )
            )
        else:
            if explicit_contaminant:
                contaminant_flag = True

    canonical_peptide = peptide
    peptide_sequence = None
    modified_peptide = None
    if modified_peptide_token:
        try:
            canonical_peptide, peptide_sequence, modified_peptide = (
                _derive_canonical_psm_peptide_fields(modified_peptide_token)
            )
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))
    elif peptide:
        try:
            canonical_peptide, peptide_sequence, modified_peptide = (
                _derive_canonical_psm_peptide_fields(peptide)
            )
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))

    if issues:
        raise ValueError(
            RejectedPsmRow(
                row_number=row_number, raw_fields=row, issues=tuple(issues)
            ).to_stable_json()
        )

    return PsmRecord(
        run_id=run_id,
        spectrum_id=spectrum_id,
        peptide=peptide,
        peptide_sequence=peptide_sequence,
        modified_peptide=modified_peptide,
        canonical_peptide=canonical_peptide,
        charge=charge,
        score=score,
        intensity=intensity,
        q_value=q_value,
        protein_refs=protein_refs,
        target_decoy_label=parse_target_decoy_label(
            protein_refs=protein_refs,
            explicit_label=explicit_label,
            policy=decoy_policy,
        ),
        contaminant_flag=contaminant_flag,
    )


def parse_psm_tsv(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV into stable records."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    accepted_records: list[PsmRecord] = []
    rejected_rows: list[RejectedPsmRow] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("PSM TSV must include a header row")
        for required_column in (
            mapping.spectrum_id,
            mapping.peptide,
            mapping.charge,
            mapping.score,
        ):
            if required_column not in reader.fieldnames:
                raise ValueError(f"missing required PSM column {required_column!r}")

        for index, row in enumerate(reader, start=2):
            normalized_row = {
                str(key): str(value) for key, value in row.items() if key is not None
            }
            try:
                accepted_records.append(
                    _parse_psm_row(
                        normalized_row,
                        row_number=index,
                        mapping=mapping,
                        decoy_policy=active_policy,
                    )
                )
            except ValueError as exc:
                rejected_rows.append(RejectedPsmRow.model_validate_json(str(exc)))

    return PsmParseReport(
        total_rows=len(accepted_records) + len(rejected_rows),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=mapping,
    )


def normalize_psm_records(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Return a stable normalized PSM ordering for downstream exports."""
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.run_id or "",
                record.spectrum_id,
                record.q_value if record.q_value is not None else float("inf"),
                -record.score,
                record.canonical_peptide,
                record.charge,
            ),
        )
    )


def export_psm_jsonl(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as stable JSONL."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(
                json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def export_psm_tsv(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as a stable TSV table."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "run_id",
                "spectrum_id",
                "peptide_sequence",
                "peptide",
                "modified_peptide",
                "canonical_peptide",
                "charge",
                "score",
                "intensity",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "contaminant_flag",
            ]
        )
        for record in normalized:
            writer.writerow(
                [
                    record.run_id or "",
                    record.spectrum_id,
                    record.peptide_sequence or "",
                    record.peptide,
                    record.modified_peptide or "",
                    record.canonical_peptide,
                    record.charge,
                    record.score,
                    "" if record.intensity is None else record.intensity,
                    "" if record.q_value is None else record.q_value,
                    ";".join(record.protein_refs),
                    record.target_decoy_label.value,
                    "true" if record.contaminant_flag else "false",
                ]
            )


def sort_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    by: PsmSortField = PsmSortField.SPECTRUM,
) -> tuple[PsmRecord, ...]:
    """Sort PSMs by one stable policy."""
    if by is PsmSortField.SPECTRUM:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.SCORE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    -record.score,
                    record.spectrum_id,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.Q_VALUE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.q_value if record.q_value is not None else float("inf"),
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.canonical_peptide,
                record.spectrum_id,
                -record.score,
            ),
        )
    )


def select_best_psm_per_spectrum(
    records: tuple[PsmRecord, ...],
) -> tuple[PsmRecord, ...]:
    """Select one best PSM per spectrum with stable tie-breaking."""
    best_by_spectrum: dict[str, PsmRecord] = {}
    for record in records:
        current = best_by_spectrum.get(record.spectrum_id)
        if current is None:
            best_by_spectrum[record.spectrum_id] = record
            continue
        replacement_key = (
            record.score,
            -(record.q_value if record.q_value is not None else float("inf")),
            -_rank_label(record.target_decoy_label),
            record.canonical_peptide,
        )
        current_key = (
            current.score,
            -(current.q_value if current.q_value is not None else float("inf")),
            -_rank_label(current.target_decoy_label),
            current.canonical_peptide,
        )
        if replacement_key > current_key:
            best_by_spectrum[record.spectrum_id] = record
    return tuple(best_by_spectrum[key] for key in sorted(best_by_spectrum))


def rollup_peptide_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[PeptideEvidenceEntry, ...]:
    """Roll up multiple PSMs into peptide-level evidence rows."""
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        grouped[record.canonical_peptide].append(record)

    rollups: list[PeptideEvidenceEntry] = []
    for canonical_peptide in sorted(grouped):
        group = grouped[canonical_peptide]
        best = max(
            group,
            key=lambda record: (
                record.score,
                -(record.q_value if record.q_value is not None else float("inf")),
                record.peptide,
            ),
        )
        protein_refs = tuple(
            sorted(
                {protein_ref for record in group for protein_ref in record.protein_refs}
            )
        )
        charge_states = tuple(sorted({record.charge for record in group}))
        spectra = {record.spectrum_id for record in group}
        q_values = [record.q_value for record in group if record.q_value is not None]
        rollups.append(
            PeptideEvidenceEntry(
                peptide=best.peptide,
                canonical_peptide=canonical_peptide,
                psm_count=len(group),
                spectrum_count=len(spectra),
                best_score=best.score,
                best_q_value=min(q_values) if q_values else None,
                charge_states=charge_states,
                protein_refs=protein_refs,
                target_decoy_label=_combine_labels(
                    tuple(record.target_decoy_label for record in group)
                ),
            )
        )
    return tuple(rollups)


def rollup_protein_evidence(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinEvidenceEntry, ...]:
    """Roll up PSMs and peptides into protein-level evidence rows."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, list[PeptideEvidenceEntry]] = defaultdict(list)
    protein_to_spectra: dict[str, set[str]] = defaultdict(set)

    record_by_peptide: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        record_by_peptide[record.canonical_peptide].append(record)

    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].append(peptide_rollup)
            for record in record_by_peptide[peptide_rollup.canonical_peptide]:
                if protein_ref in record.protein_refs:
                    protein_to_spectra[protein_ref].add(record.spectrum_id)

    rollups: list[ProteinEvidenceEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        peptides = protein_to_peptides[protein_ref]
        peptide_names = tuple(sorted(peptide.canonical_peptide for peptide in peptides))
        unique_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) == 1
        )
        shared_peptide_count = sum(
            1 for peptide in peptides if len(peptide.protein_refs) > 1
        )
        q_values = [
            peptide.best_q_value
            for peptide in peptides
            if peptide.best_q_value is not None
        ]
        rollups.append(
            ProteinEvidenceEntry(
                protein_ref=protein_ref,
                peptide_count=len(peptides),
                unique_peptide_count=unique_peptide_count,
                shared_peptide_count=shared_peptide_count,
                best_score=max(peptide.best_score for peptide in peptides),
                best_q_value=min(q_values) if q_values else None,
                peptides=peptide_names,
                spectrum_count=len(protein_to_spectra[protein_ref]),
                target_decoy_label=parse_target_decoy_label(
                    protein_refs=(protein_ref,),
                ),
            )
        )
    return tuple(rollups)


def calculate_basic_target_decoy_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> tuple[FdrAnnotatedPsm, ...]:
    """Annotate PSMs with cumulative target-decoy FDR and monotonic q-values."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")
    if tie_handling not in {"score_group", "stable_record_order"}:
        raise ValueError("tie_handling must be 'score_group' or 'stable_record_order'")
    _raise_on_target_decoy_accession_collisions(records, decoy_policy=decoy_policy)

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (
                    lambda record: (
                        -record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                    )
                )
                if score_orientation == "higher_better"
                else (
                    lambda record: (
                        record.score,
                        record.spectrum_id,
                        record.canonical_peptide,
                    )
                )
            ),
        )
    )
    annotated: list[FdrAnnotatedPsm] = []
    cumulative_targets = 0
    cumulative_decoys = 0
    score_groups: list[tuple[int, tuple[PsmRecord, ...]]] = []
    if tie_handling == "score_group":
        grouped: list[PsmRecord] = []
        current_score: float | None = None
        tie_group_rank = 0
        for record in sorted_records:
            if current_score is None or record.score == current_score:
                grouped.append(record)
                current_score = record.score
                continue
            tie_group_rank += 1
            score_groups.append((tie_group_rank, tuple(grouped)))
            grouped = [record]
            current_score = record.score
        if grouped:
            tie_group_rank += 1
            score_groups.append((tie_group_rank, tuple(grouped)))
    else:
        score_groups = [
            (rank, (record,)) for rank, record in enumerate(sorted_records, start=1)
        ]

    rank = 1
    for tie_group_rank, group in score_groups:
        group_targets = sum(
            1
            for record in group
            if record.target_decoy_label is not TargetDecoyLabel.DECOY
        )
        group_decoys = len(group) - group_targets
        cumulative_targets += group_targets
        cumulative_decoys += group_decoys
        fdr = min(cumulative_decoys / max(cumulative_targets, 1), 1.0)
        for record in group:
            annotated.append(
                FdrAnnotatedPsm(
                    psm=record,
                    rank=rank,
                    tie_group_rank=tie_group_rank,
                    tie_group_size=len(group),
                    cumulative_targets=cumulative_targets,
                    cumulative_decoys=cumulative_decoys,
                    fdr=fdr,
                    q_value=fdr,
                    accepted=threshold is None or fdr <= threshold,
                )
            )
            rank += 1

    running_min = float("inf")
    revised: list[FdrAnnotatedPsm] = []
    for entry in reversed(annotated):
        running_min = min(running_min, entry.fdr)
        revised.append(
            entry.model_copy(
                update={
                    "q_value": running_min,
                    "accepted": threshold is None or running_min <= threshold,
                }
            )
        )
    return tuple(reversed(revised))


def normalize_psm_score_orientation(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[NormalizedScoreEntry, ...]:
    """Normalize scores onto a stable best-to-worst rank scale."""
    return _normalize_calibration_score_orientation(
        tuple(
            _CalibrationEvidenceRecord(
                entity_id=record.spectrum_id,
                sort_token=record.canonical_peptide,
                score=record.score,
                q_value=record.q_value,
                target_decoy_label=record.target_decoy_label,
            )
            for record in records
        ),
        score_orientation=score_orientation,
    )


def _normalize_calibration_score_orientation(
    records: tuple[_CalibrationEvidenceRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[NormalizedScoreEntry, ...]:
    """Normalize generic calibration evidence onto a stable rank scale."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (
                    lambda record: (
                        -record.score,
                        record.entity_id,
                        record.sort_token,
                    )
                )
                if score_orientation == "higher_better"
                else (
                    lambda record: (
                        record.score,
                        record.entity_id,
                        record.sort_token,
                    )
                )
            ),
        )
    )
    if not sorted_records:
        return ()

    denominator = max(len(sorted_records) - 1, 1)
    normalized_entries: list[NormalizedScoreEntry] = []
    for rank, record in enumerate(sorted_records, start=1):
        normalized_score = (
            1.0 if len(sorted_records) == 1 else 1.0 - ((rank - 1) / denominator)
        )
        normalized_entries.append(
            NormalizedScoreEntry(
                spectrum_id=record.entity_id,
                canonical_peptide=record.sort_token,
                raw_score=record.score,
                normalized_score=normalized_score,
                rank=rank,
                target_decoy_label=record.target_decoy_label,
            )
        )
    return tuple(normalized_entries)


def _score_orientation_support_candidate(
    records: tuple[PsmRecord, ...],
    *,
    orientation: str,
    top_fraction: float,
) -> ScoreOrientationAdvisoryCandidate:
    sorted_records = _score_sorted_psm_records(
        records,
        score_orientation=orientation,
    )
    top_count = (
        max(1, math.ceil(len(sorted_records) * top_fraction)) if sorted_records else 0
    )
    top_records = sorted_records[:top_count]
    top_target_count = sum(
        1
        for record in top_records
        if record.target_decoy_label is TargetDecoyLabel.TARGET
    )
    top_decoy_count = sum(
        1
        for record in top_records
        if record.target_decoy_label is TargetDecoyLabel.DECOY
    )
    q_values = [record.q_value for record in top_records if record.q_value is not None]
    top_mean_q_value = sum(q_values) / len(q_values) if q_values else None
    labeled_count = top_target_count + top_decoy_count
    decoy_fraction = top_decoy_count / labeled_count if labeled_count else 0.5
    q_component = 1.0 - min(
        top_mean_q_value if top_mean_q_value is not None else 0.5, 1.0
    )
    support_score = max(0.0, min(1.0, ((1.0 - decoy_fraction) + q_component) / 2.0))
    return ScoreOrientationAdvisoryCandidate(
        orientation=orientation,
        top_ranked_count=top_count,
        top_target_count=top_target_count,
        top_decoy_count=top_decoy_count,
        top_mean_q_value=top_mean_q_value,
        support_score=support_score,
        note=(
            "candidate support is derived from target-decoy enrichment and q-value concentration near the top ranks"
        ),
    )


def detect_score_orientation_advisory(
    records: tuple[PsmRecord, ...],
    *,
    top_fraction: float = 0.25,
) -> ScoreOrientationAdvisory:
    """Recommend a score orientation as advisory evidence, never as an enforced rule."""
    if not 0.0 < top_fraction <= 1.0:
        raise ValueError("top_fraction must be greater than 0 and at most 1")

    higher = _score_orientation_support_candidate(
        records,
        orientation="higher_better",
        top_fraction=top_fraction,
    )
    lower = _score_orientation_support_candidate(
        records,
        orientation="lower_better",
        top_fraction=top_fraction,
    )
    sorted_candidates = sorted(
        (higher, lower),
        key=lambda candidate: (-candidate.support_score, candidate.orientation),
    )
    support_gap = (
        sorted_candidates[0].support_score - sorted_candidates[1].support_score
    )
    recommended_orientation = (
        sorted_candidates[0].orientation if support_gap >= 0.05 else None
    )
    note = (
        f"advisory evidence favors {recommended_orientation}"
        if recommended_orientation is not None
        else "advisory evidence is too balanced to recommend one score orientation"
    )
    return ScoreOrientationAdvisory(
        advisory_only=True,
        recommended_orientation=recommended_orientation,
        support_gap=support_gap,
        candidates=tuple(sorted_candidates),
        note=note,
    )


def _records_for_confidence_calibration(
    records: tuple[PsmRecord, ...],
    *,
    evidence_level: ConfidenceCalibrationLevel,
) -> tuple[_CalibrationEvidenceRecord, ...]:
    if evidence_level is ConfidenceCalibrationLevel.PSM:
        return tuple(
            _CalibrationEvidenceRecord(
                entity_id=record.spectrum_id,
                sort_token=record.canonical_peptide,
                score=record.score,
                q_value=record.q_value,
                target_decoy_label=record.target_decoy_label,
            )
            for record in records
        )
    if evidence_level is ConfidenceCalibrationLevel.PEPTIDE:
        rollups = rollup_peptide_evidence(records)
        return tuple(
            _CalibrationEvidenceRecord(
                entity_id=entry.canonical_peptide,
                sort_token=entry.canonical_peptide,
                score=entry.best_score,
                q_value=entry.best_q_value,
                target_decoy_label=entry.target_decoy_label,
            )
            for entry in rollups
        )
    protein_rollups = rollup_protein_evidence(records)
    return tuple(
        _CalibrationEvidenceRecord(
            entity_id=entry.protein_ref,
            sort_token=entry.protein_ref,
            score=entry.best_score,
            q_value=entry.best_q_value,
            target_decoy_label=entry.target_decoy_label,
        )
        for entry in protein_rollups
    )


def build_confidence_calibration_report(
    records: tuple[PsmRecord, ...],
    *,
    evidence_level: ConfidenceCalibrationLevel = ConfidenceCalibrationLevel.PSM,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> ConfidenceCalibrationReport:
    """Assess confidence with empirical calibration context beyond q-values."""
    calibration_records = _records_for_confidence_calibration(
        records,
        evidence_level=evidence_level,
    )
    calibration_plot = _build_calibration_plot_data_for_records(
        calibration_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
    )
    normalized_entries = _normalize_calibration_score_orientation(
        calibration_records,
        score_orientation=score_orientation,
    )
    q_value_by_entity_id = {
        record.entity_id: record.q_value for record in calibration_records
    }
    entries: list[ConfidenceCalibrationEntry] = []
    for entry in normalized_entries:
        bin_match = next(
            (
                calibration_bin
                for calibration_bin in calibration_plot.bins
                if calibration_bin.bin_lower <= entry.normalized_score
                and (
                    entry.normalized_score < calibration_bin.bin_upper
                    or calibration_bin.bin_upper == 1.0
                )
            ),
            calibration_plot.bins[-1] if calibration_plot.bins else None,
        )
        if bin_match is None:
            continue
        q_value = q_value_by_entity_id.get(entry.spectrum_id)
        q_component = 1.0 - min(q_value if q_value is not None else 0.5, 1.0)
        support_score = max(
            0.0,
            min(
                1.0,
                (
                    (1.0 - bin_match.decoy_fraction)
                    + entry.normalized_score
                    + q_component
                )
                / 3.0,
            ),
        )
        entries.append(
            ConfidenceCalibrationEntry(
                evidence_level=evidence_level,
                entity_id=entry.spectrum_id,
                q_value=q_value,
                normalized_score=entry.normalized_score,
                calibration_bin_lower=bin_match.bin_lower,
                calibration_bin_upper=bin_match.bin_upper,
                empirical_decoy_fraction=bin_match.decoy_fraction,
                support_score=support_score,
                note="support combines normalized rank, q-value, and empirical decoy fraction in the matched calibration bin",
            )
        )
    return ConfidenceCalibrationReport(
        evidence_level=evidence_level,
        score_orientation=score_orientation,
        entries=tuple(entries),
        calibration_plot=calibration_plot,
    )


def build_calibration_plot_data(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> CalibrationPlotData:
    """Build plot-ready score calibration bins over target-decoy evidence."""
    calibration_records = tuple(
        _CalibrationEvidenceRecord(
            entity_id=record.spectrum_id,
            sort_token=record.canonical_peptide,
            score=record.score,
            q_value=record.q_value,
            target_decoy_label=record.target_decoy_label,
        )
        for record in records
    )
    return _build_calibration_plot_data_for_records(
        calibration_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
    )


def _build_calibration_plot_data_for_records(
    records: tuple[_CalibrationEvidenceRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> CalibrationPlotData:
    """Build plot-ready score calibration bins over generic evidence rows."""
    if bin_count < 1:
        raise ValueError("bin_count must be at least 1")

    normalized_entries = _normalize_calibration_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    bins: list[CalibrationPlotBin] = []
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score <= upper
            )
        else:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score < upper
            )
        target_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.TARGET
        )
        decoy_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.DECOY
        )
        mixed_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.MIXED
        )
        unknown_count = sum(
            1
            for entry in bucket
            if entry.target_decoy_label is TargetDecoyLabel.UNKNOWN
        )
        denominator = target_count + decoy_count
        bins.append(
            CalibrationPlotBin(
                bin_lower=lower,
                bin_upper=upper,
                target_count=target_count,
                decoy_count=decoy_count,
                mixed_count=mixed_count,
                unknown_count=unknown_count,
                decoy_fraction=decoy_count / denominator if denominator else 0.0,
            )
        )
    return CalibrationPlotData(
        score_orientation=score_orientation,
        total_psms=len(records),
        bins=tuple(bins),
    )


def build_fdr_edge_case_report(
    records: tuple[PsmRecord, ...],
) -> FdrEdgeCaseReport:
    """Build an explicit report for all-target, all-decoy, and no-decoy cases."""
    target_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.TARGET
    )
    decoy_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.DECOY
    )
    mixed_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.MIXED
    )
    unknown_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.UNKNOWN
    )
    if not records:
        kind = FdrEdgeCaseKind.EMPTY
        note = "no PSM records were provided for FDR evaluation"
    elif decoy_count == 0 and target_count == len(records):
        kind = FdrEdgeCaseKind.ALL_TARGET
        note = "all records are labeled target, so target-decoy separation cannot be checked"
    elif target_count == 0 and decoy_count == len(records):
        kind = FdrEdgeCaseKind.ALL_DECOY
        note = "all records are labeled decoy, so no biological evidence can pass"
    elif decoy_count == 0:
        kind = FdrEdgeCaseKind.NO_DECOY
        note = "no decoy records are present, so FDR behavior is advisory rather than comparative"
    else:
        kind = FdrEdgeCaseKind.MIXED
        note = "target and decoy evidence are both present"
    return FdrEdgeCaseReport(
        kind=kind,
        total_records=len(records),
        target_count=target_count,
        decoy_count=decoy_count,
        mixed_count=mixed_count,
        unknown_count=unknown_count,
        note=note,
    )


def build_grouped_confidence_report(
    records: tuple[PsmRecord, ...],
    *,
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> GroupedConfidenceReport:
    """Summarize confidence over indistinguishable protein groups."""
    entries: list[GroupedConfidenceEntry] = []
    for group in build_protein_groups(records):
        q_value = group.best_q_value if group.best_q_value is not None else 1.0
        if group.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = (
                "decoy protein groups are never promoted to biological confidence"
            )
        elif q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"group q-value {q_value:.4f} is at or below the high-confidence threshold"
        elif q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"group q-value {q_value:.4f} is at or below the medium-confidence threshold"
        else:
            label = ConfidenceLabel.LOW
            explanation = f"group q-value {q_value:.4f} is reviewable but above the medium-confidence threshold"
        entries.append(
            GroupedConfidenceEntry(
                group_id=group.group_id,
                representative_protein=group.representative_protein,
                protein_refs=group.protein_refs,
                peptide_count=len(group.peptides),
                unique_peptide_count=group.unique_peptide_count,
                shared_peptide_count=group.shared_peptide_count,
                best_q_value=group.best_q_value,
                confidence_label=label,
                explanation=explanation,
            )
        )
    return GroupedConfidenceReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.group_id))
    )


def compute_fdr_reproducibility_hash(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> str:
    """Compute a stable digest over the sorted FDR derivation inputs."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    payload = {
        "score_orientation": score_orientation,
        "tie_handling": tie_handling,
        "threshold": threshold,
        "entries": [
            {
                "rank": entry.rank,
                "tie_group_rank": entry.tie_group_rank,
                "tie_group_size": entry.tie_group_size,
                "spectrum_id": entry.psm.spectrum_id,
                "canonical_peptide": entry.psm.canonical_peptide,
                "charge": entry.psm.charge,
                "score": entry.psm.score,
                "target_decoy_label": entry.psm.target_decoy_label.value,
                "cumulative_targets": entry.cumulative_targets,
                "cumulative_decoys": entry.cumulative_decoys,
                "fdr": entry.fdr,
                "q_value": entry.q_value,
                "accepted": entry.accepted,
            }
            for entry in annotated
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_fdr_audit_trail(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> FdrAuditTrail:
    """Build a stable audit trail for one target-decoy FDR calculation."""
    policy = FdrPolicy(
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        threshold=threshold,
    )
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    score_index = {
        (entry.spectrum_id, entry.canonical_peptide, entry.rank): entry
        for entry in normalized_entries
    }
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    audit_entries: list[FdrAuditEntry] = []
    for entry in annotated:
        normalized_entry = score_index.get(
            (entry.psm.spectrum_id, entry.psm.canonical_peptide, entry.rank)
        )
        audit_entries.append(
            FdrAuditEntry(
                rank=entry.rank,
                tie_group_rank=entry.tie_group_rank,
                tie_group_size=entry.tie_group_size,
                spectrum_id=entry.psm.spectrum_id,
                canonical_peptide=entry.psm.canonical_peptide,
                raw_score=entry.psm.score,
                normalized_score=normalized_entry.normalized_score
                if normalized_entry is not None
                else 0.0,
                target_decoy_label=entry.psm.target_decoy_label,
                cumulative_targets=entry.cumulative_targets,
                cumulative_decoys=entry.cumulative_decoys,
                fdr=entry.fdr,
                q_value=entry.q_value,
                accepted=entry.accepted,
            )
        )
    return FdrAuditTrail(
        policy=policy,
        entries=tuple(audit_entries),
        reproducibility_hash=compute_fdr_reproducibility_hash(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            tie_handling=tie_handling,
        ),
    )


def apply_q_values(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> tuple[PsmRecord, ...]:
    """Return PSM records with q-values filled from target-decoy FDR."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value}) for entry in annotated
    )


def filter_psms_by_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> tuple[PsmRecord, ...]:
    """Filter PSMs to those that pass the requested q-value threshold."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value})
        for entry in annotated
        if entry.accepted
    )


def build_psm_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    score_bin_size: float = 10.0,
) -> PsmSummaryReport:
    """Build a compact summary report over normalized PSM records."""
    counts_by_charge: dict[str, int] = defaultdict(int)
    counts_by_score_bin: dict[str, int] = defaultdict(int)
    target_psms = 0
    decoy_psms = 0
    mixed_psms = 0
    unknown_psms = 0
    for record in records:
        counts_by_charge[str(record.charge)] += 1
        lower = int(record.score // score_bin_size) * int(score_bin_size)
        upper = lower + int(score_bin_size)
        counts_by_score_bin[f"{lower}-{upper}"] += 1
        if record.target_decoy_label is TargetDecoyLabel.TARGET:
            target_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_psms += 1
        elif record.target_decoy_label is TargetDecoyLabel.MIXED:
            mixed_psms += 1
        else:
            unknown_psms += 1
    return PsmSummaryReport(
        total_psms=len(records),
        target_psms=target_psms,
        decoy_psms=decoy_psms,
        mixed_psms=mixed_psms,
        unknown_psms=unknown_psms,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        counts_by_score_bin=dict(sorted(counts_by_score_bin.items())),
    )


def build_peptide_summary_report(
    records: tuple[PsmRecord, ...],
) -> PeptideSummaryReport:
    """Build a compact peptide-level summary report."""
    peptide_rollups = rollup_peptide_evidence(records)
    return PeptideSummaryReport(
        total_peptides=len(peptide_rollups),
        modified_peptides=sum(
            1 for peptide in peptide_rollups if "[" in peptide.canonical_peptide
        ),
        unique_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) == 1
        ),
        shared_peptides=sum(
            1 for peptide in peptide_rollups if len(peptide.protein_refs) > 1
        ),
        decoy_peptides=sum(
            1
            for peptide in peptide_rollups
            if peptide.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )


def build_protein_summary_report(
    records: tuple[PsmRecord, ...],
    *,
    protein_lengths: dict[str, int] | None = None,
) -> ProteinSummaryReport:
    """Build a compact protein-level summary report with optional coverage."""
    rollups = rollup_protein_evidence(records)
    summary_entries: list[ProteinSummaryEntry] = []
    target_proteins = 0
    decoy_proteins = 0
    for rollup in rollups:
        coverage_fraction: float | None = None
        if protein_lengths and protein_lengths.get(rollup.protein_ref):
            covered_residues = {
                residue_index
                for peptide in rollup.peptides
                for residue_index in range(1, len(peptide) + 1)
            }
            coverage_fraction = min(
                len(covered_residues) / protein_lengths[rollup.protein_ref],
                1.0,
            )
        summary_entries.append(
            ProteinSummaryEntry(
                protein_ref=rollup.protein_ref,
                peptide_count=rollup.peptide_count,
                unique_peptide_count=rollup.unique_peptide_count,
                shared_peptide_count=rollup.shared_peptide_count,
                coverage_fraction=coverage_fraction,
            )
        )
        if rollup.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_proteins += 1
        else:
            target_proteins += 1
    return ProteinSummaryReport(
        total_proteins=len(summary_entries),
        target_proteins=target_proteins,
        decoy_proteins=decoy_proteins,
        protein_groups=tuple(summary_entries),
    )


def _entity_fdr_entries(
    entities: tuple[tuple[str, float, TargetDecoyLabel, int, tuple[str, ...]], ...],
    *,
    evidence_level: FdrEvidenceLevel,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> tuple[FdrLevelEntry, ...]:
    pseudo_records = tuple(
        PsmRecord(
            spectrum_id=entity_id,
            peptide="A",
            canonical_peptide="A",
            charge=1,
            score=score,
            protein_refs=protein_refs,
            target_decoy_label=label,
        )
        for entity_id, score, label, _member_count, protein_refs in entities
    )
    annotated = calculate_basic_target_decoy_fdr(
        pseudo_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    entity_index = {
        entity_id: (member_count, protein_refs)
        for entity_id, _score, _label, member_count, protein_refs in entities
    }
    return tuple(
        FdrLevelEntry(
            evidence_level=evidence_level,
            entity_id=entry.psm.spectrum_id,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=entity_index[entry.psm.spectrum_id][0],
            protein_refs=entity_index[entry.psm.spectrum_id][1],
        )
        for entry in annotated
    )


def _build_q_value_monotonicity_check(
    *,
    scope: str,
    entries: tuple[FdrLevelEntry, ...] | tuple[PickedProteinFdrEntry, ...],
) -> FdrQValueMonotonicityCheck:
    previous_q_value = -1.0
    first_break_rank: int | None = None
    for entry in entries:
        q_value = entry.q_value
        rank = entry.rank
        if q_value < previous_q_value:
            first_break_rank = rank
            break
        previous_q_value = q_value
    return FdrQValueMonotonicityCheck(
        scope=scope,
        entry_count=len(entries),
        valid=first_break_rank is None,
        first_break_rank=first_break_rank,
    )


def _psm_identity_key(record: PsmRecord) -> tuple[object, ...]:
    return (
        record.spectrum_id,
        record.peptide,
        record.canonical_peptide,
        record.charge,
        record.score,
        record.q_value,
        record.protein_refs,
        record.target_decoy_label.value,
    )


def _score_sorted_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    if score_orientation == "higher_better":
        key_fn = lambda record: (  # noqa: E731
            -record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    else:
        key_fn = lambda record: (  # noqa: E731
            record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    return tuple(sorted(records, key=key_fn))


def build_accepted_psm_provenance_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> AcceptedPsmProvenanceReport:
    """Build accepted-PSM provenance with explicit ranked FDR derivation state."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    normalized_by_identity: dict[tuple[object, ...], list[NormalizedScoreEntry]] = (
        defaultdict(list)
    )
    for record, entry in zip(
        _score_sorted_psm_records(records, score_orientation=score_orientation),
        normalized_entries,
        strict=True,
    ):
        normalized_by_identity[_psm_identity_key(record)].append(entry)

    accepted_entries: list[AcceptedPsmProvenanceEntry] = []
    for annotated_entry in annotated:
        if not annotated_entry.accepted:
            continue
        identity = _psm_identity_key(annotated_entry.psm)
        normalized_entry = normalized_by_identity[identity].pop(0)
        accepted_entries.append(
            AcceptedPsmProvenanceEntry(
                spectrum_id=annotated_entry.psm.spectrum_id,
                peptide=annotated_entry.psm.peptide,
                canonical_peptide=annotated_entry.psm.canonical_peptide,
                charge=annotated_entry.psm.charge,
                protein_refs=annotated_entry.psm.protein_refs,
                target_decoy_label=annotated_entry.psm.target_decoy_label,
                raw_score=annotated_entry.psm.score,
                normalized_score=normalized_entry.normalized_score,
                rank=annotated_entry.rank,
                tie_group_rank=annotated_entry.tie_group_rank,
                tie_group_size=annotated_entry.tie_group_size,
                cumulative_targets=annotated_entry.cumulative_targets,
                cumulative_decoys=annotated_entry.cumulative_decoys,
                fdr=annotated_entry.fdr,
                q_value=annotated_entry.q_value,
                threshold=threshold,
                score_orientation=score_orientation,
                score_transform="rank_normalized_psm_score",
            )
        )
    return AcceptedPsmProvenanceReport(
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        score_transform="rank_normalized_psm_score",
        entries=tuple(accepted_entries),
    )


def calculate_level_specific_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> LevelSpecificFdrReport:
    """Calculate separate PSM-, peptide-, and protein-level FDR surfaces."""
    psm_entries = tuple(
        FdrLevelEntry(
            evidence_level=FdrEvidenceLevel.PSM,
            entity_id=entry.psm.spectrum_id,
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            member_count=1,
            protein_refs=entry.psm.protein_refs,
        )
        for entry in calculate_basic_target_decoy_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            tie_handling="score_group",
            decoy_policy=None,
        )
    )
    peptide_rollups = rollup_peptide_evidence(records)
    peptide_entities = tuple(
        (
            rollup.canonical_peptide,
            rollup.best_score,
            rollup.target_decoy_label,
            rollup.psm_count,
            rollup.protein_refs,
        )
        for rollup in peptide_rollups
    )
    protein_rollups = rollup_protein_evidence(records)
    protein_entities = tuple(
        (
            rollup.protein_ref,
            rollup.best_score,
            rollup.target_decoy_label,
            rollup.peptide_count,
            (rollup.protein_ref,),
        )
        for rollup in protein_rollups
    )
    return LevelSpecificFdrReport(
        score_orientation=score_orientation,
        threshold=threshold,
        psm_entries=psm_entries,
        peptide_entries=_entity_fdr_entries(
            peptide_entities,
            evidence_level=FdrEvidenceLevel.PEPTIDE,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
        protein_entries=_entity_fdr_entries(
            protein_entities,
            evidence_level=FdrEvidenceLevel.PROTEIN,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
    )


def calculate_grouped_fdr(
    records: tuple[PsmRecord, ...],
    *,
    group_by: str,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
) -> GroupedFdrReport:
    """Calculate grouped FDR over charge state or modification state."""
    if group_by not in {"charge_state", "modification_state"}:
        raise ValueError("group_by must be 'charge_state' or 'modification_state'")
    grouped: dict[str, list[PsmRecord]] = defaultdict(list)
    for record in records:
        group_key = (
            f"z{record.charge}"
            if group_by == "charge_state"
            else ("modified" if "[" in record.canonical_peptide else "unmodified")
        )
        grouped[group_key].append(record)
    buckets = [
        GroupedFdrBucket(
            group_key=group_key,
            entries=tuple(
                FdrLevelEntry(
                    evidence_level=FdrEvidenceLevel.PSM,
                    entity_id=entry.psm.spectrum_id,
                    score=entry.psm.score,
                    q_value=entry.q_value,
                    fdr=entry.fdr,
                    rank=entry.rank,
                    accepted=entry.accepted,
                    target_decoy_label=entry.psm.target_decoy_label,
                    member_count=1,
                    protein_refs=entry.psm.protein_refs,
                )
                for entry in calculate_basic_target_decoy_fdr(
                    tuple(group_records),
                    threshold=threshold,
                    score_orientation=score_orientation,
                    tie_handling="score_group",
                    decoy_policy=None,
                )
            ),
        )
        for group_key, group_records in sorted(grouped.items())
    ]
    return GroupedFdrReport(
        group_by=group_by,
        score_orientation=score_orientation,
        threshold=threshold,
        groups=tuple(buckets),
    )


def verify_fdr_q_value_monotonicity(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> FdrQValueMonotonicityReport:
    """Verify monotonic q-values across supported FDR calculation surfaces."""
    level_report = calculate_level_specific_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    grouped_charge = calculate_grouped_fdr(
        records,
        group_by="charge_state",
        threshold=threshold,
        score_orientation=score_orientation,
    )
    grouped_modification = calculate_grouped_fdr(
        records,
        group_by="modification_state",
        threshold=threshold,
        score_orientation=score_orientation,
    )
    picked = calculate_picked_protein_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    checks = [
        _build_q_value_monotonicity_check(
            scope="psm",
            entries=level_report.psm_entries,
        ),
        _build_q_value_monotonicity_check(
            scope="peptide",
            entries=level_report.peptide_entries,
        ),
        _build_q_value_monotonicity_check(
            scope="protein",
            entries=level_report.protein_entries,
        ),
        *[
            _build_q_value_monotonicity_check(
                scope=f"grouped:{bucket.group_key}",
                entries=bucket.entries,
            )
            for report in (grouped_charge, grouped_modification)
            for bucket in report.groups
        ],
        _build_q_value_monotonicity_check(
            scope="picked_protein",
            entries=picked,
        ),
    ]
    return FdrQValueMonotonicityReport(
        valid=all(check.valid for check in checks),
        checks=tuple(checks),
    )


def build_protein_groups(
    records: tuple[PsmRecord, ...],
) -> tuple[ProteinGroupEntry, ...]:
    """Group indistinguishable proteins by their peptide evidence sets."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_to_peptides: dict[str, set[str]] = defaultdict(set)
    protein_to_scores: dict[str, list[float]] = defaultdict(list)
    protein_to_q_values: dict[str, list[float]] = defaultdict(list)
    for peptide_rollup in peptide_rollups:
        for protein_ref in peptide_rollup.protein_refs:
            protein_to_peptides[protein_ref].add(peptide_rollup.canonical_peptide)
            protein_to_scores[protein_ref].append(peptide_rollup.best_score)
            if peptide_rollup.best_q_value is not None:
                protein_to_q_values[protein_ref].append(peptide_rollup.best_q_value)

    grouped: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for protein_ref, peptides in protein_to_peptides.items():
        grouped[tuple(sorted(peptides))].append(protein_ref)

    entries: list[ProteinGroupEntry] = []
    for index, (peptide_set, protein_refs) in enumerate(
        sorted(grouped.items()), start=1
    ):
        sorted_proteins = tuple(sorted(protein_refs))
        representative = sorted_proteins[0]
        entries.append(
            ProteinGroupEntry(
                group_id=f"pg-{index:03d}",
                representative_protein=representative,
                protein_refs=sorted_proteins,
                peptides=tuple(peptide_set),
                unique_peptide_count=sum(
                    1
                    for peptide in peptide_set
                    if len(
                        next(
                            rollup.protein_refs
                            for rollup in peptide_rollups
                            if rollup.canonical_peptide == peptide
                        )
                    )
                    == 1
                ),
                shared_peptide_count=sum(
                    1
                    for peptide in peptide_set
                    if len(
                        next(
                            rollup.protein_refs
                            for rollup in peptide_rollups
                            if rollup.canonical_peptide == peptide
                        )
                    )
                    > 1
                ),
                best_score=max(
                    protein_to_scores[protein_ref][0]
                    if len(protein_to_scores[protein_ref]) == 1
                    else max(protein_to_scores[protein_ref])
                    for protein_ref in sorted_proteins
                ),
                best_q_value=min(
                    (
                        q_value
                        for protein_ref in sorted_proteins
                        for q_value in protein_to_q_values[protein_ref]
                    ),
                    default=None,
                ),
                target_decoy_label=_combine_labels(
                    tuple(
                        parse_target_decoy_label(protein_refs=(protein_ref,))
                        for protein_ref in sorted_proteins
                    )
                ),
            )
        )
    return tuple(entries)


def build_shared_peptide_ambiguity_report(
    records: tuple[PsmRecord, ...],
) -> SharedPeptideAmbiguityReport:
    """Explain why protein groups remain ambiguous under shared peptide evidence."""
    peptide_rollups = {
        rollup.canonical_peptide: rollup for rollup in rollup_peptide_evidence(records)
    }
    entries: list[SharedPeptideAmbiguityEntry] = []
    for group in build_protein_groups(records):
        shared_peptides = tuple(
            sorted(
                peptide
                for peptide in group.peptides
                if len(peptide_rollups[peptide].protein_refs) > 1
            )
        )
        if not shared_peptides and len(group.protein_refs) == 1:
            continue
        unique_peptides = tuple(
            sorted(
                peptide
                for peptide in group.peptides
                if len(peptide_rollups[peptide].protein_refs) == 1
            )
        )
        outside_group_proteins = tuple(
            sorted(
                {
                    protein_ref
                    for peptide in shared_peptides
                    for protein_ref in peptide_rollups[peptide].protein_refs
                    if protein_ref not in group.protein_refs
                }
            )
        )
        if len(group.protein_refs) > 1 and outside_group_proteins:
            reason = SharedPeptideAmbiguityReason.MIXED
            explanation = f"group {group.group_id} has indistinguishable members and shared peptides that also map outside the group"
        elif len(group.protein_refs) > 1:
            reason = SharedPeptideAmbiguityReason.INDISTINGUISHABLE_MEMBERS
            explanation = f"group {group.group_id} contains proteins with the same observed peptide evidence"
        else:
            reason = SharedPeptideAmbiguityReason.EXTERNAL_SHARED_PEPTIDES
            explanation = f"group {group.group_id} is connected to outside proteins only through shared peptide evidence"
        entries.append(
            SharedPeptideAmbiguityEntry(
                group_id=group.group_id,
                protein_refs=group.protein_refs,
                shared_peptides=shared_peptides,
                unique_peptides=unique_peptides,
                outside_group_proteins=outside_group_proteins,
                reason=reason,
                explanation=explanation,
            )
        )
    return SharedPeptideAmbiguityReport(entries=tuple(entries))


def assign_razor_peptides(
    records: tuple[PsmRecord, ...],
) -> tuple[RazorPeptideAssignment, ...]:
    """Assign shared peptides to one representative protein by razor rules."""
    peptide_rollups = rollup_peptide_evidence(records)
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1

    assignments: list[RazorPeptideAssignment] = []
    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        candidates = tuple(sorted(rollup.protein_refs))
        if not candidates:
            continue
        rationale = "unique_peptide"
        assigned = candidates[0]
        if len(candidates) > 1:
            ranked = sorted(
                candidates,
                key=lambda protein_ref: (
                    -unique_counts.get(protein_ref, 0),
                    -best_scores.get(protein_ref, float("-inf")),
                    protein_ref,
                ),
            )
            assigned = ranked[0]
            if unique_counts.get(ranked[0], 0) != unique_counts.get(ranked[-1], 0):
                rationale = "unique_evidence_priority"
            elif best_scores.get(ranked[0], 0.0) != best_scores.get(ranked[-1], 0.0):
                rationale = "best_score_tiebreak"
            else:
                rationale = "lexicographic_tiebreak"
        assignments.append(
            RazorPeptideAssignment(
                canonical_peptide=rollup.canonical_peptide,
                candidate_proteins=candidates,
                assigned_protein=assigned,
                rationale=rationale,
            )
        )
    return tuple(assignments)


def build_razor_peptide_provenance_report(
    records: tuple[PsmRecord, ...],
) -> RazorPeptideProvenanceReport:
    """Build an explicit provenance report for razor peptide assignments."""
    peptide_rollups = rollup_peptide_evidence(records)
    unique_counts: dict[str, int] = defaultdict(int)
    best_scores: dict[str, float] = defaultdict(float)
    for rollup in peptide_rollups:
        for protein_ref in rollup.protein_refs:
            best_scores[protein_ref] = max(best_scores[protein_ref], rollup.best_score)
        if len(rollup.protein_refs) == 1:
            unique_counts[rollup.protein_refs[0]] += 1

    assignments = {
        entry.canonical_peptide: entry for entry in assign_razor_peptides(records)
    }
    entries: list[RazorPeptideProvenanceEntry] = []
    for rollup in sorted(peptide_rollups, key=lambda entry: entry.canonical_peptide):
        assignment = assignments.get(rollup.canonical_peptide)
        if assignment is None:
            continue
        entries.append(
            RazorPeptideProvenanceEntry(
                canonical_peptide=rollup.canonical_peptide,
                candidate_proteins=assignment.candidate_proteins,
                assigned_protein=assignment.assigned_protein,
                rationale=assignment.rationale,
                candidate_unique_peptide_counts={
                    protein_ref: unique_counts.get(protein_ref, 0)
                    for protein_ref in assignment.candidate_proteins
                },
                candidate_best_scores={
                    protein_ref: best_scores.get(protein_ref, 0.0)
                    for protein_ref in assignment.candidate_proteins
                },
            )
        )
    return RazorPeptideProvenanceReport(
        policy_name="unique_peptide_then_best_score_then_lexicographic",
        tie_break_order=(
            "unique_peptide_count",
            "best_score",
            "protein_accession",
        ),
        entries=tuple(entries),
    )


def build_combined_evidence_report(
    records: tuple[PsmRecord, ...],
    *,
    ptm_site_keys_by_peptide: dict[str, tuple[str, ...]] | None = None,
    quant_support_by_protein: dict[str, dict[str, float | None]] | None = None,
    parsimony_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> CombinedEvidenceReport:
    """Join identification evidence with optional PTM and quant support."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_groups = build_protein_groups(records)
    groups_by_protein = {
        protein_ref: group
        for group in protein_groups
        for protein_ref in group.protein_refs
    }
    selected_variants_by_protein: dict[str, set[ParsimonyVariant]] = defaultdict(set)
    for variant in parsimony_variants:
        for entry in infer_proteins_by_parsimony(records, variant=variant):
            selected_variants_by_protein[entry.protein_ref].add(variant)

    entries: list[CombinedEvidenceEntry] = []
    for rollup in peptide_rollups:
        ptm_site_keys = tuple(
            sorted((ptm_site_keys_by_peptide or {}).get(rollup.canonical_peptide, ()))
        )
        quant_lookup = quant_support_by_protein or {}
        for protein_ref in rollup.protein_refs:
            group = groups_by_protein.get(protein_ref)
            entries.append(
                CombinedEvidenceEntry(
                    canonical_peptide=rollup.canonical_peptide,
                    protein_ref=protein_ref,
                    spectrum_ids=tuple(
                        sorted(
                            record.spectrum_id
                            for record in records
                            if record.canonical_peptide == rollup.canonical_peptide
                        )
                    ),
                    psm_count=rollup.psm_count,
                    best_psm_q_value=rollup.best_q_value,
                    peptide_charge_states=rollup.charge_states,
                    protein_group_id=group.group_id if group is not None else None,
                    protein_group_members=group.protein_refs
                    if group is not None
                    else (),
                    parsimony_variants=tuple(
                        sorted(
                            selected_variants_by_protein.get(protein_ref, set()),
                            key=lambda item: item.value,
                        )
                    ),
                    ptm_site_keys=ptm_site_keys,
                    quant_support=tuple(
                        CombinedEvidenceQuantSupport(
                            sample_id=sample_id,
                            abundance=abundance,
                        )
                        for sample_id, abundance in sorted(
                            quant_lookup.get(protein_ref, {}).items()
                        )
                    ),
                )
            )
    return CombinedEvidenceReport(
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (entry.canonical_peptide, entry.protein_ref),
            )
        )
    )


def build_peptide_protein_trace_report(
    records: tuple[PsmRecord, ...],
) -> PeptideProteinTraceReport:
    """Build stable peptide-to-protein traces that survive export."""
    peptide_rollups = rollup_peptide_evidence(records)
    protein_groups = build_protein_groups(records)
    group_ids_by_protein: dict[str, set[str]] = defaultdict(set)
    for group in protein_groups:
        for protein_ref in group.protein_refs:
            group_ids_by_protein[protein_ref].add(group.group_id)

    entries: list[PeptideProteinTraceEntry] = []
    for rollup in peptide_rollups:
        spectrum_ids = tuple(
            sorted(
                record.spectrum_id
                for record in records
                if record.canonical_peptide == rollup.canonical_peptide
            )
        )
        group_ids = tuple(
            sorted(
                {
                    group_id
                    for protein_ref in rollup.protein_refs
                    for group_id in group_ids_by_protein.get(protein_ref, set())
                }
            )
        )
        entries.append(
            PeptideProteinTraceEntry(
                canonical_peptide=rollup.canonical_peptide,
                peptide=rollup.peptide,
                spectrum_ids=spectrum_ids,
                protein_refs=rollup.protein_refs,
                protein_group_ids=group_ids,
                charge_states=rollup.charge_states,
                best_score=rollup.best_score,
                best_q_value=rollup.best_q_value,
            )
        )
    return PeptideProteinTraceReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.canonical_peptide, entry.peptide))
        )
    )


def export_peptide_protein_trace_jsonl(
    report: PeptideProteinTraceReport,
    path: Path,
) -> None:
    """Write a stable JSONL export for peptide-to-protein traces."""
    with path.open("w", encoding="utf-8") as handle:
        for entry in report.entries:
            handle.write(
                json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def export_peptide_protein_trace_tsv(
    report: PeptideProteinTraceReport,
    path: Path,
) -> None:
    """Write a stable TSV export for peptide-to-protein traces."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "canonical_peptide",
                "peptide",
                "spectrum_ids",
                "protein_refs",
                "protein_group_ids",
                "charge_states",
                "best_score",
                "best_q_value",
            ]
        )
        for entry in report.entries:
            writer.writerow(
                [
                    entry.canonical_peptide,
                    entry.peptide,
                    ";".join(entry.spectrum_ids),
                    ";".join(entry.protein_refs),
                    ";".join(entry.protein_group_ids),
                    ";".join(str(charge) for charge in entry.charge_states),
                    entry.best_score,
                    "" if entry.best_q_value is None else entry.best_q_value,
                ]
            )


def build_inference_disagreement_report(
    records: tuple[PsmRecord, ...],
    *,
    parsimony_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> InferenceDisagreementReport:
    """Expose disagreements across inference strategies instead of hiding them."""
    peptide_rollups = rollup_peptide_evidence(records)
    razor = {entry.canonical_peptide: entry for entry in assign_razor_peptides(records)}
    parsimony_results = {
        variant: infer_proteins_by_parsimony(records, variant=variant)
        for variant in parsimony_variants
    }
    entries: list[InferenceDisagreementEntry] = []
    for rollup in peptide_rollups:
        if len(rollup.protein_refs) < 2:
            continue
        assignments: dict[str, tuple[str, ...]] = {}
        razor_assignment = razor.get(rollup.canonical_peptide)
        if razor_assignment is not None:
            assignments["razor"] = (razor_assignment.assigned_protein,)
        for variant, selected in parsimony_results.items():
            assignments[f"parsimony:{variant.value}"] = tuple(
                entry.protein_ref
                for entry in selected
                if rollup.canonical_peptide in entry.covered_peptides
            )
        flattened = {
            protein_ref
            for protein_refs in assignments.values()
            for protein_ref in protein_refs
        }
        if len(flattened) > 1:
            entries.append(
                InferenceDisagreementEntry(
                    subject_id=rollup.canonical_peptide,
                    kind=InferenceDisagreementKind.PEPTIDE_ASSIGNMENT,
                    strategy_assignments=assignments,
                    note="shared peptide support diverges across razor and parsimony strategies",
                )
            )

    comparison = compare_parsimony_variants(records, variants=parsimony_variants)
    for difference in comparison.differences:
        if (
            not difference.left_only_proteins
            and not difference.right_only_proteins
            and difference.first_difference_rank is None
        ):
            continue
        entries.append(
            InferenceDisagreementEntry(
                subject_id=f"{difference.left_variant.value}__vs__{difference.right_variant.value}",
                kind=InferenceDisagreementKind.PROTEIN_SET,
                strategy_assignments={
                    difference.left_variant.value: tuple(
                        entry.protein_ref
                        for entry in parsimony_results[difference.left_variant]
                    ),
                    difference.right_variant.value: tuple(
                        entry.protein_ref
                        for entry in parsimony_results[difference.right_variant]
                    ),
                },
                note="named parsimony variants diverge in protein-set membership or ranking over the same evidence",
            )
        )
    return InferenceDisagreementReport(
        entries=tuple(
            sorted(entries, key=lambda entry: (entry.kind.value, entry.subject_id))
        )
    )


def _parsimony_sort_key(
    group: ProteinGroupEntry,
    newly_explained: tuple[str, ...],
    variant: ParsimonyVariant,
) -> tuple[float | int | str, ...]:
    if variant is ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY:
        return (
            -group.unique_peptide_count,
            -len(newly_explained),
            -group.best_score,
            group.representative_protein,
        )
    if variant is ParsimonyVariant.BEST_SCORE_PRIORITY:
        return (
            -group.best_score,
            -len(newly_explained),
            -group.unique_peptide_count,
            group.representative_protein,
        )
    return (
        -len(newly_explained),
        -group.unique_peptide_count,
        -group.best_score,
        group.representative_protein,
    )


def infer_proteins_by_parsimony(
    records: tuple[PsmRecord, ...],
    *,
    variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
) -> tuple[ParsimonyProteinEntry, ...]:
    """Greedily select a parsimonious protein set that explains observed peptides."""
    protein_groups = build_protein_groups(records)
    remaining = {
        peptide.canonical_peptide
        for peptide in rollup_peptide_evidence(records)
        if peptide.target_decoy_label is not TargetDecoyLabel.DECOY
    }
    selected: list[ParsimonyProteinEntry] = []
    available = list(protein_groups)
    rank = 1
    while remaining:
        scored_candidates = []
        for group in available:
            newly_explained = tuple(sorted(set(group.peptides) & remaining))
            if not newly_explained:
                continue
            scored_candidates.append((group, newly_explained))
        if not scored_candidates:
            break
        scored_candidates.sort(
            key=lambda item: _parsimony_sort_key(item[0], item[1], variant)
        )
        group, newly_explained = scored_candidates[0]
        selected.append(
            ParsimonyProteinEntry(
                variant=variant,
                selection_rank=rank,
                protein_ref=group.representative_protein,
                source_group_id=group.group_id,
                covered_peptides=group.peptides,
                newly_explained_peptides=newly_explained,
                best_score=group.best_score,
                best_q_value=group.best_q_value,
                target_decoy_label=group.target_decoy_label,
            )
        )
        remaining -= set(newly_explained)
        available = [entry for entry in available if entry.group_id != group.group_id]
        rank += 1
    return tuple(selected)


def compare_parsimony_variants(
    records: tuple[PsmRecord, ...],
    *,
    variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> ParsimonyVariantComparisonReport:
    """Compare multiple named parsimony policies over the same PSM evidence."""
    results = tuple(
        ParsimonyVariantResult(
            variant=variant,
            selected_proteins=infer_proteins_by_parsimony(records, variant=variant),
        )
        for variant in variants
    )
    differences: list[ParsimonyVariantDifferenceEntry] = []
    for left_index, left in enumerate(results):
        for right in results[left_index + 1 :]:
            left_order = [entry.protein_ref for entry in left.selected_proteins]
            right_order = [entry.protein_ref for entry in right.selected_proteins]
            first_difference_rank = next(
                (
                    rank
                    for rank, (left_ref, right_ref) in enumerate(
                        zip(left_order, right_order, strict=False),
                        start=1,
                    )
                    if left_ref != right_ref
                ),
                None,
            )
            if first_difference_rank is None and len(left_order) != len(right_order):
                first_difference_rank = min(len(left_order), len(right_order)) + 1
            left_set = set(left_order)
            right_set = set(right_order)
            differences.append(
                ParsimonyVariantDifferenceEntry(
                    left_variant=left.variant,
                    right_variant=right.variant,
                    first_difference_rank=first_difference_rank,
                    shared_selected_proteins=tuple(sorted(left_set & right_set)),
                    left_only_proteins=tuple(sorted(left_set - right_set)),
                    right_only_proteins=tuple(sorted(right_set - left_set)),
                )
            )
    return ParsimonyVariantComparisonReport(
        results=results,
        differences=tuple(differences),
    )


def build_protein_coverage_map(
    records: tuple[PsmRecord, ...],
    *,
    protein_sequences: dict[str, str],
) -> tuple[ProteinCoverageEntry, ...]:
    """Build a sequence-aware coverage map for proteins present in evidence."""
    peptide_sequences = {
        record.canonical_peptide: record.peptide_sequence
        or _derive_canonical_psm_peptide_fields(record.canonical_peptide)[1]
        for record in records
    }
    protein_to_peptides: dict[str, set[str]] = defaultdict(set)
    for rollup in rollup_peptide_evidence(records):
        for protein_ref in rollup.protein_refs:
            protein_to_peptides[protein_ref].add(
                peptide_sequences[rollup.canonical_peptide]
            )

    coverage_entries: list[ProteinCoverageEntry] = []
    for protein_ref in sorted(protein_to_peptides):
        sequence = protein_sequences.get(protein_ref)
        if not sequence:
            continue
        covered_positions: set[int] = set()
        covered_ranges: set[tuple[int, int]] = set()
        for peptide in sorted(protein_to_peptides[protein_ref]):
            start = sequence.find(peptide)
            while start != -1:
                end = start + len(peptide)
                covered_ranges.add((start + 1, end))
                covered_positions.update(range(start + 1, end + 1))
                start = sequence.find(peptide, start + 1)
        coverage_entries.append(
            ProteinCoverageEntry(
                protein_ref=protein_ref,
                residue_count=len(sequence),
                covered_residue_count=len(covered_positions),
                coverage_fraction=min(len(covered_positions) / len(sequence), 1.0)
                if sequence
                else 0.0,
                covered_ranges=tuple(sorted(covered_ranges)),
                covered_peptides=tuple(sorted(protein_to_peptides[protein_ref])),
            )
        )
    return tuple(coverage_entries)


def build_peptide_uniqueness_across_database(
    peptides: tuple[str, ...],
    *,
    protein_sequences: dict[str, str],
) -> tuple[DatabasePeptideUniquenessEntry, ...]:
    """Classify peptide uniqueness by direct lookup across a provided database."""
    entries: list[DatabasePeptideUniquenessEntry] = []
    for peptide in sorted(dict.fromkeys(peptides)):
        matching_proteins = tuple(
            sorted(
                protein_ref
                for protein_ref, sequence in protein_sequences.items()
                if peptide in sequence
            )
        )
        entries.append(
            DatabasePeptideUniquenessEntry(
                canonical_peptide=peptide,
                protein_refs=matching_proteins,
                uniqueness=(
                    DatabasePeptideUniqueness.UNIQUE
                    if len(matching_proteins) == 1
                    else DatabasePeptideUniqueness.SHARED
                    if len(matching_proteins) > 1
                    else DatabasePeptideUniqueness.MISSING
                ),
            )
        )
    return tuple(entries)


def calculate_picked_protein_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> tuple[PickedProteinFdrEntry, ...]:
    """Calculate picked protein FDR by pairing targets and decoys with the same base accession."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    protein_rollups = rollup_protein_evidence(records)

    def _base_accession(protein_ref: str) -> str:
        value = protein_ref
        if active_policy.protein_prefix and value.startswith(
            active_policy.protein_prefix
        ):
            value = value[len(active_policy.protein_prefix) :]
        if active_policy.protein_suffix and value.endswith(
            active_policy.protein_suffix
        ):
            value = value[: -len(active_policy.protein_suffix)]
        return value

    paired: dict[str, list[ProteinEvidenceEntry]] = defaultdict(list)
    for rollup in protein_rollups:
        paired[_base_accession(rollup.protein_ref)].append(rollup)

    selected_entities: list[
        tuple[str, float, TargetDecoyLabel, tuple[str, ...], str | None]
    ] = []
    for _base_accession_key, entries in sorted(paired.items()):
        sorted_entries = sorted(
            entries,
            key=lambda entry: (
                -entry.best_score
                if score_orientation == "higher_better"
                else entry.best_score,
                entry.protein_ref,
            ),
        )
        winner = sorted_entries[0]
        partner_ref = next(
            (
                entry.protein_ref
                for entry in sorted_entries[1:]
                if entry.target_decoy_label is not winner.target_decoy_label
            ),
            None,
        )
        selected_entities.append(
            (
                winner.protein_ref,
                winner.best_score,
                winner.target_decoy_label,
                winner.peptides,
                partner_ref,
            )
        )

    pseudo_records = tuple(
        PsmRecord(
            spectrum_id=protein_ref,
            peptide="A",
            canonical_peptide="A",
            charge=1,
            score=score,
            protein_refs=(protein_ref,),
            target_decoy_label=label,
        )
        for protein_ref, score, label, _peptides, _partner in selected_entities
    )
    annotated = calculate_basic_target_decoy_fdr(
        pseudo_records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling="score_group",
        decoy_policy=active_policy,
    )
    selected_index = {
        protein_ref: (peptides, partner_ref)
        for protein_ref, _score, _label, peptides, partner_ref in selected_entities
    }
    return tuple(
        PickedProteinFdrEntry(
            protein_ref=entry.psm.spectrum_id,
            partner_ref=selected_index[entry.psm.spectrum_id][1],
            score=entry.psm.score,
            q_value=entry.q_value,
            fdr=entry.fdr,
            rank=entry.rank,
            accepted=entry.accepted,
            target_decoy_label=entry.psm.target_decoy_label,
            supporting_peptides=selected_index[entry.psm.spectrum_id][0],
        )
        for entry in annotated
    )


def assign_confidence_labels(
    entries: tuple[PickedProteinFdrEntry, ...],
    *,
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> tuple[ConfidenceAssignment, ...]:
    """Assign high/medium/low confidence labels from q-valued protein evidence."""
    assignments: list[ConfidenceAssignment] = []
    for entry in entries:
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = "decoy evidence is never promoted to biological confidence"
        elif entry.q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"q-value {entry.q_value:.4f} is at or below the high-confidence threshold"
        elif entry.q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"q-value {entry.q_value:.4f} is at or below the medium-confidence threshold"
        elif entry.accepted:
            label = ConfidenceLabel.LOW
            explanation = f"q-value {entry.q_value:.4f} passes FDR but misses the medium-confidence threshold"
        else:
            label = ConfidenceLabel.REJECTED
            explanation = f"q-value {entry.q_value:.4f} does not pass the requested acceptance threshold"
        assignments.append(
            ConfidenceAssignment(
                entity_id=entry.protein_ref,
                q_value=entry.q_value,
                label=label,
                explanation=explanation,
            )
        )
    return tuple(assignments)


def _assign_level_specific_confidence(
    entries: tuple[FdrLevelEntry, ...],
    *,
    evidence_level: FdrEvidenceLevel,
    high_threshold: float,
    medium_threshold: float,
) -> tuple[LevelSpecificConfidenceAssignment, ...]:
    assignments: list[LevelSpecificConfidenceAssignment] = []
    for entry in entries:
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            label = ConfidenceLabel.DECOY
            explanation = "decoy evidence is never promoted to biological confidence"
        elif entry.q_value <= high_threshold:
            label = ConfidenceLabel.HIGH
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} is at or below the high-confidence threshold"
        elif entry.q_value <= medium_threshold:
            label = ConfidenceLabel.MEDIUM
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} is at or below the medium-confidence threshold"
        elif entry.accepted:
            label = ConfidenceLabel.LOW
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} passes FDR but misses the medium-confidence threshold"
        else:
            label = ConfidenceLabel.REJECTED
            explanation = f"{evidence_level.value} q-value {entry.q_value:.4f} does not pass the requested acceptance threshold"
        assignments.append(
            LevelSpecificConfidenceAssignment(
                evidence_level=evidence_level,
                entity_id=entry.entity_id,
                q_value=entry.q_value,
                label=label,
                explanation=explanation,
            )
        )
    return tuple(assignments)


def assign_level_specific_confidence_labels(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = 0.05,
    score_orientation: str = "higher_better",
    high_threshold: float = 0.01,
    medium_threshold: float = 0.05,
) -> LevelSpecificConfidenceReport:
    """Assign separate confidence labels for PSM, peptide, and protein evidence."""
    level_report = calculate_level_specific_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    return LevelSpecificConfidenceReport(
        psm_assignments=_assign_level_specific_confidence(
            level_report.psm_entries,
            evidence_level=FdrEvidenceLevel.PSM,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
        peptide_assignments=_assign_level_specific_confidence(
            level_report.peptide_entries,
            evidence_level=FdrEvidenceLevel.PEPTIDE,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
        protein_assignments=_assign_level_specific_confidence(
            level_report.protein_entries,
            evidence_level=FdrEvidenceLevel.PROTEIN,
            high_threshold=high_threshold,
            medium_threshold=medium_threshold,
        ),
    )


def build_confidence_threshold_sensitivity_report(
    records: tuple[PsmRecord, ...],
    *,
    thresholds: tuple[float, ...] = (0.001, 0.01, 0.05, 0.1),
    score_orientation: str = "higher_better",
) -> ConfidenceThresholdSensitivityReport:
    """Report how accepted evidence changes across explicit FDR cutoffs."""
    normalized_thresholds = tuple(sorted(dict.fromkeys(thresholds)))
    if any(threshold < 0.0 or threshold > 1.0 for threshold in normalized_thresholds):
        raise ValueError("thresholds must be between 0 and 1")

    entries: list[ConfidenceThresholdSensitivityEntry] = []
    previous_psms: set[str] = set()
    previous_peptides: set[str] = set()
    previous_proteins: set[str] = set()
    previous_picked: set[str] = set()

    for threshold in normalized_thresholds:
        level_report = calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        picked = calculate_picked_protein_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        accepted_psms = {
            entry.entity_id for entry in level_report.psm_entries if entry.accepted
        }
        accepted_peptides = {
            entry.entity_id for entry in level_report.peptide_entries if entry.accepted
        }
        accepted_proteins = {
            entry.entity_id for entry in level_report.protein_entries if entry.accepted
        }
        accepted_picked = {entry.protein_ref for entry in picked if entry.accepted}
        entries.append(
            ConfidenceThresholdSensitivityEntry(
                threshold=threshold,
                accepted_psm_count=len(accepted_psms),
                accepted_peptide_count=len(accepted_peptides),
                accepted_protein_count=len(accepted_proteins),
                accepted_picked_protein_count=len(accepted_picked),
                newly_accepted_psm_ids=tuple(sorted(accepted_psms - previous_psms)),
                newly_accepted_peptides=tuple(
                    sorted(accepted_peptides - previous_peptides)
                ),
                newly_accepted_proteins=tuple(
                    sorted(accepted_proteins - previous_proteins)
                ),
                newly_accepted_picked_proteins=tuple(
                    sorted(accepted_picked - previous_picked)
                ),
            )
        )
        previous_psms = accepted_psms
        previous_peptides = accepted_peptides
        previous_proteins = accepted_proteins
        previous_picked = accepted_picked

    return ConfidenceThresholdSensitivityReport(
        score_orientation=score_orientation,
        thresholds=normalized_thresholds,
        entries=tuple(entries),
    )


def build_review_ready_evidence_bundle(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float = 0.05,
    score_orientation: str = "higher_better",
    ptm_site_keys_by_peptide: dict[str, tuple[str, ...]] | None = None,
    quant_support_by_protein: dict[str, dict[str, float | None]] | None = None,
) -> ReviewReadyEvidenceBundle:
    """Build a review-ready evidence bundle without requiring raw search output."""
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="review_ready_evidence_bundle",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    bundle = ReviewReadyEvidenceBundle(
        document_schema=schema,
        threshold=threshold,
        score_orientation=score_orientation,
        psm_summary=build_psm_summary_report(records),
        peptide_summary=build_peptide_summary_report(records),
        protein_summary=build_protein_summary_report(records),
        accepted_psm_provenance=build_accepted_psm_provenance_report(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
        grouped_confidence=build_grouped_confidence_report(records),
        combined_evidence=build_combined_evidence_report(
            records,
            ptm_site_keys_by_peptide=ptm_site_keys_by_peptide,
            quant_support_by_protein=quant_support_by_protein,
        ),
        peptide_traces=build_peptide_protein_trace_report(records),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def export_review_ready_evidence_bundle(
    bundle: ReviewReadyEvidenceBundle,
    path: Path,
) -> None:
    """Write a stable JSON evidence bundle for downstream review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def build_search_result_provenance_manifest(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    decoy_policy: TargetDecoyLabelPolicy,
    fdr_policy: FdrPolicy | None = None,
) -> SearchResultProvenanceManifest:
    """Build a stable provenance manifest for one parsed search-result table."""
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=source_sha256,
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    payload = manifest.to_dict()
    return manifest.model_copy(
        update={"document_schema": manifest.document_schema.with_content_hash(payload)}
    )
