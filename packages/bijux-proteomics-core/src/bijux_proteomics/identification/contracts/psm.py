# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""PSM, target-decoy, and search-result record contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.chemistry.modifications import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    TargetDecoyState,
)
from bijux_proteomics.domain.records import (
    ModifiedPeptide as CanonicalModifiedPeptide,
)
from bijux_proteomics.domain.records import (
    PeptideRecord as CanonicalPeptideRecord,
)
from bijux_proteomics.domain.records import (
    ProteinGroup as CanonicalProteinGroup,
)
from bijux_proteomics.domain.records import (
    ProteinRecord as CanonicalProteinRecord,
)
from bijux_proteomics.domain.records import (
    PSMRecord as CanonicalPsmRecord,
)
from bijux_proteomics.domain.records import (
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class TargetDecoyLabel(StrEnum):
    """Normalized target/decoy state for one evidence record."""

    TARGET = "target"
    DECOY = "decoy"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class TargetDecoyContaminantClass(StrEnum):
    """Unified evidence class across target, decoy, and contaminant semantics."""

    TARGET = "target"
    DECOY = "decoy"
    CONTAMINANT = "contaminant"
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
    posterior_error_probability: str | None = None
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


class TargetDecoyContaminantClassification(JsonModel):
    """Unified classification plus compatibility fields for one evidence row."""

    model_config = ConfigDict(extra="forbid")

    target_decoy_contaminant_class: TargetDecoyContaminantClass
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool
    target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    decoy_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    contaminant_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


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
    posterior_error_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    local_fdr: float | None = Field(default=None, ge=0.0, le=1.0)
    error_rate_provenance: str | None = Field(default=None, min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    contaminant_flag: bool = False
    target_decoy_contaminant_class: TargetDecoyContaminantClass = (
        TargetDecoyContaminantClass.UNKNOWN
    )
    provenance: ImportedEvidenceProvenance | None = None

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
        classification = classify_target_decoy_contaminant(
            protein_refs=self.protein_refs,
            target_decoy_label=self.target_decoy_label,
            explicit_contaminant_label=self.contaminant_flag,
        )
        self.target_decoy_label = classification.target_decoy_label
        self.contaminant_flag = classification.contaminant_flag
        self.target_decoy_contaminant_class = (
            classification.target_decoy_contaminant_class
        )
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
            metadata={
                "source_contract": "identification.psm_record",
                **(
                    {
                        "posterior_error_probability": str(
                            self.posterior_error_probability
                        )
                    }
                    if self.posterior_error_probability is not None
                    else {}
                ),
                **(
                    {"local_fdr": str(self.local_fdr)}
                    if self.local_fdr is not None
                    else {}
                ),
                **(
                    {"error_rate_provenance": self.error_rate_provenance}
                    if self.error_rate_provenance is not None
                    else {}
                ),
                **(
                    self.provenance.to_metadata_fields()
                    if self.provenance is not None
                    else {}
                ),
            },
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
                dict.fromkeys(
                    modification.name for modification in parsed.modifications
                )
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

        issue_message = (
            "; ".join(issue.message for issue in self.issues) or "rejected psm row"
        )
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


def _is_contaminant_protein_ref(
    protein_ref: str,
    *,
    contaminant_prefixes: tuple[str, ...],
) -> bool:
    return any(protein_ref.startswith(prefix) for prefix in contaminant_prefixes)


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


def _normalize_target_decoy_label_token(
    value: str | TargetDecoyLabel | None,
    *,
    protein_refs: tuple[str, ...],
    policy: TargetDecoyLabelPolicy,
) -> TargetDecoyLabel:
    if isinstance(value, TargetDecoyLabel):
        return value
    return parse_target_decoy_label(
        protein_refs=protein_refs,
        explicit_label=value,
        policy=policy,
    )


def classify_target_decoy_contaminant(
    *,
    protein_refs: tuple[str, ...] = (),
    target_decoy_label: str | TargetDecoyLabel | None = None,
    explicit_contaminant_label: str | bool | None = None,
    policy: TargetDecoyLabelPolicy | None = None,
    contaminant_prefixes: tuple[str, ...] = ("CON__",),
) -> TargetDecoyContaminantClassification:
    """Classify evidence using target-decoy, contaminant, and accession semantics."""

    active_policy = policy or TargetDecoyLabelPolicy()
    normalized_target_decoy_label = _normalize_target_decoy_label_token(
        target_decoy_label,
        protein_refs=protein_refs,
        policy=active_policy,
    )

    if isinstance(explicit_contaminant_label, bool):
        contaminant_from_label = explicit_contaminant_label
    else:
        contaminant_from_label = bool(
            _parse_contaminant_label(explicit_contaminant_label)
        )

    target_protein_refs: list[str] = []
    decoy_protein_refs: list[str] = []
    contaminant_protein_refs: list[str] = []
    for protein_ref in protein_refs:
        if _is_contaminant_protein_ref(
            protein_ref,
            contaminant_prefixes=contaminant_prefixes,
        ):
            contaminant_protein_refs.append(protein_ref)
            continue
        per_ref_label = parse_target_decoy_label(
            protein_refs=(protein_ref,),
            policy=active_policy,
        )
        if per_ref_label is TargetDecoyLabel.DECOY:
            decoy_protein_refs.append(protein_ref)
        else:
            target_protein_refs.append(protein_ref)

    has_target = bool(target_protein_refs)
    has_decoy = bool(decoy_protein_refs)
    has_contaminant = bool(contaminant_protein_refs) or contaminant_from_label is True

    if normalized_target_decoy_label is TargetDecoyLabel.MIXED:
        has_target = True
        has_decoy = True
    elif normalized_target_decoy_label is TargetDecoyLabel.DECOY:
        has_decoy = True
    elif (
        normalized_target_decoy_label is TargetDecoyLabel.TARGET
        and not contaminant_protein_refs
    ):
        has_target = True

    active_class_count = sum((has_target, has_decoy, has_contaminant))
    if active_class_count == 0:
        target_decoy_contaminant_class = TargetDecoyContaminantClass.UNKNOWN
    elif active_class_count > 1:
        target_decoy_contaminant_class = TargetDecoyContaminantClass.MIXED
    elif has_contaminant:
        target_decoy_contaminant_class = TargetDecoyContaminantClass.CONTAMINANT
    elif has_decoy:
        target_decoy_contaminant_class = TargetDecoyContaminantClass.DECOY
    else:
        target_decoy_contaminant_class = TargetDecoyContaminantClass.TARGET

    return TargetDecoyContaminantClassification(
        target_decoy_contaminant_class=target_decoy_contaminant_class,
        target_decoy_label=normalized_target_decoy_label,
        contaminant_flag=has_contaminant,
        target_protein_refs=tuple(target_protein_refs),
        decoy_protein_refs=tuple(decoy_protein_refs),
        contaminant_protein_refs=tuple(contaminant_protein_refs),
    )


def is_biological_foreground_class(
    value: TargetDecoyContaminantClass | TargetDecoyContaminantClassification,
) -> bool:
    """Return whether one unified evidence class belongs to biological foreground."""

    evidence_class = (
        value.target_decoy_contaminant_class
        if isinstance(value, TargetDecoyContaminantClassification)
        else value
    )
    return evidence_class is TargetDecoyContaminantClass.TARGET


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


__all__ = [
    "TargetDecoyLabel",
    "TargetDecoyContaminantClass",
    "PsmSortField",
    "SearchResultColumnMapping",
    "TargetDecoyLabelPolicy",
    "TargetDecoyContaminantClassification",
    "PsmRecord",
    "SearchResultValidationIssue",
    "RejectedPsmRow",
    "PsmParseReport",
    "TargetDecoyCollisionEntry",
    "TargetDecoyCollisionReport",
    "DecoyStrategyValidationIssue",
    "DecoyStrategyValidationReport",
    "classify_target_decoy_contaminant",
    "is_biological_foreground_class",
    "validate_target_decoy_policy",
    "parse_target_decoy_label",
    "validate_target_decoy_accession_collisions",
]
