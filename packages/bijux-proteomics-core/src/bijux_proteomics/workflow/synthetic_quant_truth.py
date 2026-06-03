# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Synthetic quant-truth datasets for benchmarking quantification methods."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class SyntheticQuantSample(JsonModel):
    """One synthetic study sample with condition and batch structure."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate: int = Field(..., ge=1)
    batch_id: str = Field(..., min_length=1)


class SyntheticQuantProteinSpec(JsonModel):
    """One non-contaminant protein carried through the synthetic dataset."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_ids: tuple[str, ...] = Field(..., min_length=1)
    baseline_log2_intensity: float


class SyntheticQuantChangedProteinSpec(SyntheticQuantProteinSpec):
    """One protein with a known condition effect."""

    effect_log2_fold_change: float


class SyntheticQuantBatchEffectSpec(JsonModel):
    """One known batch-specific protein shift."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    batch_id: str = Field(..., min_length=1)
    log2_shift: float


class SyntheticQuantMissingnessSpec(JsonModel):
    """One known missingness signal over one protein or peptide subset."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(..., min_length=1)
    peptide_id: str | None = None
    reason: str = Field(default="synthetic_missingness", min_length=1)


class SyntheticQuantPeptideOutlierSpec(JsonModel):
    """One known peptide-specific outlier event."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    log2_shift: float


class SyntheticQuantContaminationSpec(JsonModel):
    """One known contaminant protein signal."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_ids: tuple[str, ...] = Field(..., min_length=1)
    baseline_log2_intensity: float
    sample_ids: tuple[str, ...] = Field(..., min_length=1)
    contaminant_class: str = Field(..., min_length=1)


class SyntheticQuantTruthConfig(JsonModel):
    """Configuration for one deterministic synthetic quant-truth dataset."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    reference_condition: str = Field(..., min_length=1)
    effect_condition: str = Field(..., min_length=1)
    samples: tuple[SyntheticQuantSample, ...] = Field(..., min_length=2)
    changed_proteins: tuple[SyntheticQuantChangedProteinSpec, ...] = Field(
        default_factory=tuple
    )
    unchanged_proteins: tuple[SyntheticQuantProteinSpec, ...] = Field(
        default_factory=tuple
    )
    batch_effects: tuple[SyntheticQuantBatchEffectSpec, ...] = Field(
        default_factory=tuple
    )
    missingness: tuple[SyntheticQuantMissingnessSpec, ...] = Field(
        default_factory=tuple
    )
    peptide_outliers: tuple[SyntheticQuantPeptideOutlierSpec, ...] = Field(
        default_factory=tuple
    )
    contamination: tuple[SyntheticQuantContaminationSpec, ...] = Field(
        default_factory=tuple
    )
    peptide_bias_step: float = Field(default=0.2, ge=0.0)
    replicate_jitter_step: float = Field(default=0.05, ge=0.0)


class SyntheticQuantPeptideObservation(JsonModel):
    """One peptide-level observation with explicit injected signal audit fields."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate: int = Field(..., ge=1)
    batch_id: str = Field(..., min_length=1)
    log2_intensity: float | None = None
    is_missing: bool = False
    is_contaminant: bool = False
    contaminant_class: str | None = None
    applied_condition_log2_effect: float = 0.0
    applied_batch_log2_shift: float = 0.0
    applied_outlier_log2_shift: float = 0.0


class SyntheticQuantTruthRecord(JsonModel):
    """One exact truth row carried beside the generated quantitative observations."""

    model_config = ConfigDict(extra="forbid")

    truth_id: str = Field(..., min_length=1)
    truth_kind: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    peptide_id: str | None = None
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    batch_ids: tuple[str, ...] = Field(default_factory=tuple)
    effect_log2_fold_change: float | None = None
    shift_log2: float | None = None
    contaminant_class: str | None = None
    reason: str | None = None


class SyntheticQuantTruthDataset(JsonModel):
    """One deterministic synthetic benchmark dataset for quant-method truth checks."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    reference_condition: str = Field(..., min_length=1)
    effect_condition: str = Field(..., min_length=1)
    samples: tuple[SyntheticQuantSample, ...] = Field(default_factory=tuple)
    peptide_observations: tuple[SyntheticQuantPeptideObservation, ...] = Field(
        default_factory=tuple
    )
    truth_records: tuple[SyntheticQuantTruthRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def generate_quant_truth_dataset(
    config: SyntheticQuantTruthConfig,
) -> SyntheticQuantTruthDataset:
    """Generate a deterministic peptide-level quant dataset with exact truth rows."""

    _validate_and_index_config(config)
    sample_offsets = _sample_condition_offsets(
        config.samples,
        jitter_step=config.replicate_jitter_step,
    )
    batch_shifts = {
        (entry.protein_id, entry.batch_id): entry.log2_shift
        for entry in config.batch_effects
    }
    missing_by_key: dict[tuple[str, str | None], set[str]] = {}
    for entry in config.missingness:
        missing_by_key.setdefault((entry.protein_id, entry.peptide_id), set()).update(
            entry.sample_ids
        )
    outlier_by_key = {
        (entry.protein_id, entry.peptide_id, entry.sample_id): entry.log2_shift
        for entry in config.peptide_outliers
    }

    observations: list[SyntheticQuantPeptideObservation] = []
    truth_records: list[SyntheticQuantTruthRecord] = []

    for protein in config.changed_proteins:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=f"changed_protein:{protein.protein_id}",
                truth_kind="changed_protein",
                subject_id=protein.protein_id,
                protein_id=protein.protein_id,
                effect_log2_fold_change=protein.effect_log2_fold_change,
            )
        )
        observations.extend(
            _protein_observations(
                protein_id=protein.protein_id,
                peptide_ids=protein.peptide_ids,
                baseline_log2_intensity=protein.baseline_log2_intensity,
                effect_condition=config.effect_condition,
                effect_log2_fold_change=protein.effect_log2_fold_change,
                samples=config.samples,
                sample_offsets=sample_offsets,
                batch_shifts=batch_shifts,
                missing_by_key=missing_by_key,
                outlier_by_key=outlier_by_key,
                peptide_bias_step=config.peptide_bias_step,
            )
        )

    for unchanged_protein in config.unchanged_proteins:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=f"unchanged_protein:{unchanged_protein.protein_id}",
                truth_kind="unchanged_protein",
                subject_id=unchanged_protein.protein_id,
                protein_id=unchanged_protein.protein_id,
                effect_log2_fold_change=0.0,
            )
        )
        observations.extend(
            _protein_observations(
                protein_id=unchanged_protein.protein_id,
                peptide_ids=unchanged_protein.peptide_ids,
                baseline_log2_intensity=unchanged_protein.baseline_log2_intensity,
                effect_condition=config.effect_condition,
                effect_log2_fold_change=0.0,
                samples=config.samples,
                sample_offsets=sample_offsets,
                batch_shifts=batch_shifts,
                missing_by_key=missing_by_key,
                outlier_by_key=outlier_by_key,
                peptide_bias_step=config.peptide_bias_step,
            )
        )

    for batch_effect in config.batch_effects:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=f"batch_effect:{batch_effect.protein_id}:{batch_effect.batch_id}",
                truth_kind="batch_effect",
                subject_id=f"{batch_effect.protein_id}:{batch_effect.batch_id}",
                protein_id=batch_effect.protein_id,
                batch_ids=(batch_effect.batch_id,),
                shift_log2=batch_effect.log2_shift,
            )
        )

    for missingness_entry in config.missingness:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=_missingness_truth_id(missingness_entry),
                truth_kind="missingness",
                subject_id=_missingness_subject_id(missingness_entry),
                protein_id=missingness_entry.protein_id,
                peptide_id=missingness_entry.peptide_id,
                sample_ids=missingness_entry.sample_ids,
                reason=missingness_entry.reason,
            )
        )

    for peptide_outlier in config.peptide_outliers:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=f"peptide_outlier:{peptide_outlier.protein_id}:{peptide_outlier.peptide_id}:{peptide_outlier.sample_id}",
                truth_kind="peptide_outlier",
                subject_id=f"{peptide_outlier.protein_id}:{peptide_outlier.peptide_id}:{peptide_outlier.sample_id}",
                protein_id=peptide_outlier.protein_id,
                peptide_id=peptide_outlier.peptide_id,
                sample_ids=(peptide_outlier.sample_id,),
                shift_log2=peptide_outlier.log2_shift,
            )
        )

    for contamination_entry in config.contamination:
        truth_records.append(
            SyntheticQuantTruthRecord(
                truth_id=f"contamination:{contamination_entry.protein_id}",
                truth_kind="contamination",
                subject_id=contamination_entry.protein_id,
                protein_id=contamination_entry.protein_id,
                sample_ids=contamination_entry.sample_ids,
                contaminant_class=contamination_entry.contaminant_class,
            )
        )
        observations.extend(
            _contaminant_observations(
                spec=contamination_entry,
                samples=config.samples,
                sample_offsets=sample_offsets,
                peptide_bias_step=config.peptide_bias_step,
            )
        )

    return SyntheticQuantTruthDataset(
        dataset_id=config.dataset_id,
        reference_condition=config.reference_condition,
        effect_condition=config.effect_condition,
        samples=config.samples,
        peptide_observations=tuple(observations),
        truth_records=tuple(truth_records),
        note=(
            "synthetic quant-truth dataset preserves exact injected truth rows beside "
            "deterministic peptide observations for quant-method benchmarking"
        ),
    )


def render_synthetic_quant_samples_tsv(
    dataset: SyntheticQuantTruthDataset,
) -> str:
    """Render synthetic sample design rows as TSV."""

    rows = [
        {
            "sample_id": sample.sample_id,
            "condition": sample.condition,
            "replicate": str(sample.replicate),
            "batch_id": sample.batch_id,
        }
        for sample in dataset.samples
    ]
    return _render_tsv(
        rows,
        fieldnames=("sample_id", "condition", "replicate", "batch_id"),
    )


def render_synthetic_quant_peptide_observation_tsv(
    dataset: SyntheticQuantTruthDataset,
) -> str:
    """Render peptide-level synthetic observations as TSV."""

    rows = [
        {
            "protein_id": row.protein_id,
            "peptide_id": row.peptide_id,
            "sample_id": row.sample_id,
            "condition": row.condition,
            "replicate": str(row.replicate),
            "batch_id": row.batch_id,
            "log2_intensity": "" if row.log2_intensity is None else f"{row.log2_intensity:.4f}",
            "is_missing": "true" if row.is_missing else "false",
            "is_contaminant": "true" if row.is_contaminant else "false",
            "contaminant_class": row.contaminant_class or "",
            "applied_condition_log2_effect": f"{row.applied_condition_log2_effect:.4f}",
            "applied_batch_log2_shift": f"{row.applied_batch_log2_shift:.4f}",
            "applied_outlier_log2_shift": f"{row.applied_outlier_log2_shift:.4f}",
        }
        for row in dataset.peptide_observations
    ]
    return _render_tsv(
        rows,
        fieldnames=(
            "protein_id",
            "peptide_id",
            "sample_id",
            "condition",
            "replicate",
            "batch_id",
            "log2_intensity",
            "is_missing",
            "is_contaminant",
            "contaminant_class",
            "applied_condition_log2_effect",
            "applied_batch_log2_shift",
            "applied_outlier_log2_shift",
        ),
    )


def render_synthetic_quant_truth_tsv(
    dataset: SyntheticQuantTruthDataset,
) -> str:
    """Render exact injected truth rows as TSV."""

    rows = [
        {
            "truth_id": row.truth_id,
            "truth_kind": row.truth_kind,
            "subject_id": row.subject_id,
            "protein_id": row.protein_id,
            "peptide_id": row.peptide_id or "",
            "sample_ids": ",".join(row.sample_ids),
            "batch_ids": ",".join(row.batch_ids),
            "effect_log2_fold_change": (
                "" if row.effect_log2_fold_change is None else f"{row.effect_log2_fold_change:.4f}"
            ),
            "shift_log2": "" if row.shift_log2 is None else f"{row.shift_log2:.4f}",
            "contaminant_class": row.contaminant_class or "",
            "reason": row.reason or "",
        }
        for row in dataset.truth_records
    ]
    return _render_tsv(
        rows,
        fieldnames=(
            "truth_id",
            "truth_kind",
            "subject_id",
            "protein_id",
            "peptide_id",
            "sample_ids",
            "batch_ids",
            "effect_log2_fold_change",
            "shift_log2",
            "contaminant_class",
            "reason",
        ),
    )


def _validate_and_index_config(
    config: SyntheticQuantTruthConfig,
) -> dict[str, object]:
    sample_ids = [sample.sample_id for sample in config.samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("synthetic quant truth config requires unique sample ids")
    condition_ids = {sample.condition for sample in config.samples}
    if config.reference_condition not in condition_ids:
        raise ValueError(
            f"synthetic quant truth reference condition {config.reference_condition!r} is not present in samples"
        )
    if config.effect_condition not in condition_ids:
        raise ValueError(
            f"synthetic quant truth effect condition {config.effect_condition!r} is not present in samples"
        )
    if config.reference_condition == config.effect_condition:
        raise ValueError("synthetic quant truth requires distinct reference and effect conditions")

    known_proteins: dict[str, set[str]] = {}
    for protein in (*config.changed_proteins, *config.unchanged_proteins):
        if protein.protein_id in known_proteins:
            raise ValueError(
                f"synthetic quant truth protein {protein.protein_id!r} is declared more than once"
            )
        if len(protein.peptide_ids) != len(set(protein.peptide_ids)):
            raise ValueError(
                f"synthetic quant truth protein {protein.protein_id!r} contains duplicate peptide ids"
            )
        known_proteins[protein.protein_id] = set(protein.peptide_ids)

    contaminant_ids = {entry.protein_id for entry in config.contamination}
    if contaminant_ids & set(known_proteins):
        overlap = ", ".join(sorted(contaminant_ids & set(known_proteins)))
        raise ValueError(
            "synthetic quant truth contamination proteins must not overlap biological proteins: "
            f"{overlap}"
        )
    for entry in config.contamination:
        if len(entry.peptide_ids) != len(set(entry.peptide_ids)):
            raise ValueError(
                f"synthetic quant truth contaminant {entry.protein_id!r} contains duplicate peptide ids"
            )
        unknown_samples = set(entry.sample_ids) - set(sample_ids)
        if unknown_samples:
            raise ValueError(
                f"synthetic quant truth contaminant {entry.protein_id!r} references unknown samples: "
                + ", ".join(sorted(unknown_samples))
            )

    known_batches = {sample.batch_id for sample in config.samples}
    for batch_effect in config.batch_effects:
        if batch_effect.protein_id not in known_proteins:
            raise ValueError(
                f"synthetic quant truth batch effect references unknown protein {batch_effect.protein_id!r}"
            )
        if batch_effect.batch_id not in known_batches:
            raise ValueError(
                f"synthetic quant truth batch effect references unknown batch {batch_effect.batch_id!r}"
            )
    for missingness_entry in config.missingness:
        _validate_known_peptide_scope(
            known_proteins=known_proteins,
            protein_id=missingness_entry.protein_id,
            peptide_id=missingness_entry.peptide_id,
            error_prefix="synthetic quant truth missingness",
        )
        unknown_samples = set(missingness_entry.sample_ids) - set(sample_ids)
        if unknown_samples:
            raise ValueError(
                "synthetic quant truth missingness references unknown samples: "
                + ", ".join(sorted(unknown_samples))
            )
    for peptide_outlier in config.peptide_outliers:
        _validate_known_peptide_scope(
            known_proteins=known_proteins,
            protein_id=peptide_outlier.protein_id,
            peptide_id=peptide_outlier.peptide_id,
            error_prefix="synthetic quant truth peptide outlier",
            require_peptide=True,
        )
        if peptide_outlier.sample_id not in sample_ids:
            raise ValueError(
                f"synthetic quant truth peptide outlier references unknown sample {peptide_outlier.sample_id!r}"
            )
    return {
        "known_proteins": known_proteins,
    }


def _validate_known_peptide_scope(
    *,
    known_proteins: dict[str, set[str]],
    protein_id: str,
    peptide_id: str | None,
    error_prefix: str,
    require_peptide: bool = False,
) -> None:
    if protein_id not in known_proteins:
        raise ValueError(f"{error_prefix} references unknown protein {protein_id!r}")
    if peptide_id is None:
        if require_peptide:
            raise ValueError(f"{error_prefix} requires an explicit peptide id")
        return
    if peptide_id not in known_proteins[protein_id]:
        raise ValueError(
            f"{error_prefix} references unknown peptide {peptide_id!r} for protein {protein_id!r}"
        )


def _sample_condition_offsets(
    samples: tuple[SyntheticQuantSample, ...],
    *,
    jitter_step: float,
) -> dict[str, float]:
    per_condition: dict[str, list[SyntheticQuantSample]] = {}
    for sample in samples:
        per_condition.setdefault(sample.condition, []).append(sample)
    offsets: dict[str, float] = {}
    for condition, condition_samples in per_condition.items():
        midpoint = (len(condition_samples) - 1) / 2
        for index, sample in enumerate(condition_samples):
            offsets[sample.sample_id] = (index - midpoint) * jitter_step
    return offsets


def _protein_observations(
    *,
    protein_id: str,
    peptide_ids: tuple[str, ...],
    baseline_log2_intensity: float,
    effect_condition: str,
    effect_log2_fold_change: float,
    samples: tuple[SyntheticQuantSample, ...],
    sample_offsets: dict[str, float],
    batch_shifts: dict[tuple[str, str], float],
    missing_by_key: dict[tuple[str, str | None], set[str]],
    outlier_by_key: dict[tuple[str, str, str], float],
    peptide_bias_step: float,
) -> list[SyntheticQuantPeptideObservation]:
    midpoint = (len(peptide_ids) - 1) / 2
    observations: list[SyntheticQuantPeptideObservation] = []
    for peptide_index, peptide_id in enumerate(peptide_ids):
        peptide_bias = (peptide_index - midpoint) * peptide_bias_step
        for sample in samples:
            condition_effect = (
                effect_log2_fold_change if sample.condition == effect_condition else 0.0
            )
            batch_shift = batch_shifts.get((protein_id, sample.batch_id), 0.0)
            outlier_shift = outlier_by_key.get((protein_id, peptide_id, sample.sample_id), 0.0)
            is_missing = sample.sample_id in missing_by_key.get((protein_id, peptide_id), set()) or sample.sample_id in missing_by_key.get((protein_id, None), set())
            intensity = None
            if not is_missing:
                intensity = (
                    baseline_log2_intensity
                    + peptide_bias
                    + sample_offsets[sample.sample_id]
                    + condition_effect
                    + batch_shift
                    + outlier_shift
                )
            observations.append(
                SyntheticQuantPeptideObservation(
                    protein_id=protein_id,
                    peptide_id=peptide_id,
                    sample_id=sample.sample_id,
                    condition=sample.condition,
                    replicate=sample.replicate,
                    batch_id=sample.batch_id,
                    log2_intensity=intensity,
                    is_missing=is_missing,
                    is_contaminant=False,
                    applied_condition_log2_effect=condition_effect,
                    applied_batch_log2_shift=batch_shift,
                    applied_outlier_log2_shift=outlier_shift,
                )
            )
    return observations


def _contaminant_observations(
    *,
    spec: SyntheticQuantContaminationSpec,
    samples: tuple[SyntheticQuantSample, ...],
    sample_offsets: dict[str, float],
    peptide_bias_step: float,
) -> list[SyntheticQuantPeptideObservation]:
    midpoint = (len(spec.peptide_ids) - 1) / 2
    active_samples = set(spec.sample_ids)
    observations: list[SyntheticQuantPeptideObservation] = []
    for peptide_index, peptide_id in enumerate(spec.peptide_ids):
        peptide_bias = (peptide_index - midpoint) * peptide_bias_step
        for sample in samples:
            if sample.sample_id not in active_samples:
                continue
            observations.append(
                SyntheticQuantPeptideObservation(
                    protein_id=spec.protein_id,
                    peptide_id=peptide_id,
                    sample_id=sample.sample_id,
                    condition=sample.condition,
                    replicate=sample.replicate,
                    batch_id=sample.batch_id,
                    log2_intensity=(
                        spec.baseline_log2_intensity
                        + peptide_bias
                        + sample_offsets[sample.sample_id]
                    ),
                    is_missing=False,
                    is_contaminant=True,
                    contaminant_class=spec.contaminant_class,
                    applied_condition_log2_effect=0.0,
                    applied_batch_log2_shift=0.0,
                    applied_outlier_log2_shift=0.0,
                )
            )
    return observations


def _missingness_truth_id(entry: SyntheticQuantMissingnessSpec) -> str:
    sample_scope = ",".join(entry.sample_ids)
    if entry.peptide_id is None:
        return f"missingness:{entry.protein_id}:{sample_scope}"
    return f"missingness:{entry.protein_id}:{entry.peptide_id}:{sample_scope}"


def _missingness_subject_id(entry: SyntheticQuantMissingnessSpec) -> str:
    if entry.peptide_id is None:
        return entry.protein_id
    return f"{entry.protein_id}:{entry.peptide_id}"


def _render_tsv(
    rows: list[dict[str, str]],
    *,
    fieldnames: tuple[str, ...],
) -> str:
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return handle.getvalue()
