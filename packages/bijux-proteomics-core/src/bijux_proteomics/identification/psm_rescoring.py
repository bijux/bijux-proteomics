# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Target-decoy logistic rescoring for spectrum-derived PSM feature tables."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from typing import Literal

import numpy as np
from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.psm_features import PsmFeatureRow
from bijux_proteomics_foundation import JsonModel

FeatureTransform = Literal["identity", "absolute"]

_FEATURE_SPECIFICATIONS: tuple[tuple[str, FeatureTransform], ...] = (
    ("score_native", "identity"),
    ("charge", "identity"),
    ("peptide_length", "identity"),
    ("missed_cleavages", "identity"),
    ("precursor_ppm_error", "absolute"),
    ("matched_ion_count", "identity"),
    ("explained_intensity", "identity"),
    ("spectrum_entropy", "identity"),
    ("top_peak_unmatched_fraction", "identity"),
)


class PsmRescoringFeatureParameter(JsonModel):
    """One standardized model feature with its durable fitted weight."""

    model_config = ConfigDict(extra="forbid")

    feature_name: str = Field(..., min_length=1)
    transform: FeatureTransform
    mean: float
    scale: float = Field(..., gt=0.0)
    weight: float


class PsmRescoringModel(JsonModel):
    """Fitted logistic rescoring model without external ML dependencies."""

    model_config = ConfigDict(extra="forbid")

    intercept: float
    feature_parameters: tuple[PsmRescoringFeatureParameter, ...] = Field(
        default_factory=tuple
    )
    regularization_strength: float = Field(..., ge=0.0)
    iteration_count: int = Field(..., ge=1)
    convergence_delta: float = Field(..., ge=0.0)
    native_auc: float = Field(..., ge=0.0, le=1.0)
    rescored_auc: float = Field(..., ge=0.0, le=1.0)


class PsmRescoringEntry(JsonModel):
    """One PSM row after logistic target-decoy rescoring."""

    model_config = ConfigDict(extra="forbid")

    psm_id: str = Field(..., min_length=1)
    rescored_probability: float = Field(..., ge=0.0, le=1.0)
    rescored_score: float
    rescored_q_value: float = Field(..., ge=0.0, le=1.0)
    native_q_value: float | None = Field(default=None, ge=0.0)
    rank_before: int = Field(..., ge=1)
    rank_after: int = Field(..., ge=1)


class PsmRescoringExplanationEntry(JsonModel):
    """One per-feature contribution row for a rescored PSM."""

    model_config = ConfigDict(extra="forbid")

    psm_id: str = Field(..., min_length=1)
    feature_name: str = Field(..., min_length=1)
    feature_value: float
    standardized_value: float
    model_weight: float
    signed_contribution: float


class PsmRescoringSummary(JsonModel):
    """Compact audit summary for one logistic rescoring run."""

    model_config = ConfigDict(extra="forbid")

    total_psm_count: int = Field(..., ge=0)
    target_psm_count: int = Field(..., ge=0)
    decoy_psm_count: int = Field(..., ge=0)
    q_values_monotonic: bool
    native_auc: float = Field(..., ge=0.0, le=1.0)
    rescored_auc: float = Field(..., ge=0.0, le=1.0)
    separation_gain: float


class PsmRescoringReport(JsonModel):
    """Complete target-decoy rescoring result over one feature table."""

    model_config = ConfigDict(extra="forbid")

    model: PsmRescoringModel
    summary: PsmRescoringSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[PsmRescoringEntry, ...] = Field(default_factory=tuple)


def fit_target_decoy_logistic_model(
    feature_table: tuple[PsmFeatureRow, ...],
    *,
    regularization_strength: float = 0.01,
    max_iterations: int = 200,
    tolerance: float = 1e-6,
) -> PsmRescoringReport:
    """Fit one standardized target-decoy logistic rescoring model.

    The fit is intentionally implemented in pure Python and NumPy so the core
    owner does not depend on sklearn for PSM rescoring.
    """

    if not feature_table:
        raise ValueError("feature_table must not be empty")
    if regularization_strength < 0.0:
        raise ValueError("regularization_strength must be non-negative")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least one")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be greater than zero")

    labels = np.array([_binary_label(row.target_decoy_label) for row in feature_table])
    if np.any(labels < 0):
        raise ValueError("feature_table must contain only target or decoy labels")
    target_count = int(np.sum(labels == 1.0))
    decoy_count = int(np.sum(labels == 0.0))
    if target_count == 0 or decoy_count == 0:
        raise ValueError("feature_table must contain both target and decoy labels")

    feature_parameters = _build_feature_parameters(feature_table)
    feature_matrix = np.vstack(
        [
            _project_feature_row(
                row=row,
                feature_parameters=feature_parameters,
            )
            for row in feature_table
        ]
    )
    if np.allclose(feature_matrix, 0.0):
        raise ValueError("insufficient_target_decoy_separation")

    native_scores = np.array([row.score_native for row in feature_table], dtype=float)
    native_auc = _binary_auc(native_scores, labels)
    native_rank = _rank_map(
        (
            (row.psm_id, row.score_native)
            for row in feature_table
        ),
        higher_better=True,
    )

    fitted_parameters, iteration_count, convergence_delta = _fit_logistic_parameters(
        feature_matrix,
        labels,
        regularization_strength=regularization_strength,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    rescored_probabilities = _sigmoid(
        fitted_parameters[0] + feature_matrix @ fitted_parameters[1:]
    )
    rescored_auc = _binary_auc(rescored_probabilities, labels)
    if (
        rescored_auc <= 0.55
        or np.mean(rescored_probabilities[labels == 1.0])
        <= np.mean(rescored_probabilities[labels == 0.0]) + 0.02
    ):
        raise ValueError("insufficient_target_decoy_separation")

    rescored_scores = _logit(rescored_probabilities)
    rescored_rank = _rank_map(
        (
            (row.psm_id, score)
            for row, score in zip(feature_table, rescored_scores, strict=True)
        ),
        higher_better=True,
    )
    rescored_q_values = _rescored_q_values(
        feature_table=feature_table,
        rescored_scores=rescored_scores,
    )
    model = PsmRescoringModel(
        intercept=float(fitted_parameters[0]),
        feature_parameters=tuple(
            parameter.model_copy(update={"weight": float(weight)})
            for parameter, weight in zip(
                feature_parameters,
                fitted_parameters[1:],
                strict=True,
            )
        ),
        regularization_strength=regularization_strength,
        iteration_count=iteration_count,
        convergence_delta=convergence_delta,
        native_auc=native_auc,
        rescored_auc=rescored_auc,
    )
    entries = tuple(
        sorted(
            (
                PsmRescoringEntry(
                    psm_id=row.psm_id,
                    rescored_probability=float(probability),
                    rescored_score=float(score),
                    rescored_q_value=rescored_q_values[row.psm_id],
                    native_q_value=row.q_value_native,
                    rank_before=native_rank[row.psm_id],
                    rank_after=rescored_rank[row.psm_id],
                )
                for row, probability, score in zip(
                    feature_table,
                    rescored_probabilities,
                    rescored_scores,
                    strict=True,
                )
            ),
            key=lambda entry: entry.rank_after,
        )
    )
    summary = PsmRescoringSummary(
        total_psm_count=len(entries),
        target_psm_count=target_count,
        decoy_psm_count=decoy_count,
        q_values_monotonic=all(
            left.rescored_q_value <= right.rescored_q_value
            for left, right in zip(entries, entries[1:], strict=False)
        ),
        native_auc=native_auc,
        rescored_auc=rescored_auc,
        separation_gain=rescored_auc - native_auc,
    )
    return PsmRescoringReport(
        model=model,
        summary=summary,
        reproducibility_hash=hashlib.sha256(
            _rescoring_payload(model=model, entries=entries)
        ).hexdigest(),
        entries=entries,
    )


def explain_rescored_psm(
    model: PsmRescoringModel,
    feature_row: PsmFeatureRow,
) -> tuple[PsmRescoringExplanationEntry, ...]:
    """Explain one rescored PSM with the fitted feature contributions."""

    _validate_model_feature_parameters(model.feature_parameters)
    entries = []
    for parameter in model.feature_parameters:
        raw_value = _feature_row_value(feature_row, parameter.feature_name)
        standardized_value = _standardize_feature_value(
            value=raw_value,
            parameter=parameter,
        )
        entries.append(
            PsmRescoringExplanationEntry(
                psm_id=feature_row.psm_id,
                feature_name=parameter.feature_name,
                feature_value=raw_value,
                standardized_value=standardized_value,
                model_weight=parameter.weight,
                signed_contribution=standardized_value * parameter.weight,
            )
        )
    return tuple(entries)


def render_psm_rescoring_tsv(report: PsmRescoringReport) -> str:
    """Render rescored PSM rows with before-versus-after ranks."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "psm_id",
            "rescored_probability",
            "rescored_score",
            "rescored_q_value",
            "native_q_value",
            "rank_before",
            "rank_after",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.psm_id,
                entry.rescored_probability,
                entry.rescored_score,
                entry.rescored_q_value,
                "" if entry.native_q_value is None else entry.native_q_value,
                entry.rank_before,
                entry.rank_after,
            )
        )
    return buffer.getvalue()


def render_psm_rescoring_explanation_tsv(
    entries: tuple[PsmRescoringExplanationEntry, ...],
) -> str:
    """Render per-feature rescoring contributions for one PSM as TSV."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "psm_id",
            "feature_name",
            "feature_value",
            "standardized_value",
            "model_weight",
            "signed_contribution",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.psm_id,
                entry.feature_name,
                entry.feature_value,
                entry.standardized_value,
                entry.model_weight,
                entry.signed_contribution,
            )
        )
    return buffer.getvalue()


def _build_feature_parameters(
    feature_table: tuple[PsmFeatureRow, ...],
) -> tuple[PsmRescoringFeatureParameter, ...]:
    parameters: list[PsmRescoringFeatureParameter] = []
    for feature_name, transform in _FEATURE_SPECIFICATIONS:
        transformed = np.array(
            [
                _transform_feature_value(
                    value=float(getattr(row, feature_name)),
                    transform=transform,
                )
                for row in feature_table
            ],
            dtype=float,
        )
        mean = float(np.mean(transformed))
        scale = float(np.std(transformed))
        if scale <= 1e-12:
            scale = 1.0
        parameters.append(
            PsmRescoringFeatureParameter(
                feature_name=feature_name,
                transform=transform,
                mean=mean,
                scale=scale,
                weight=0.0,
            )
        )
    return tuple(parameters)


def _project_feature_row(
    *,
    row: PsmFeatureRow,
    feature_parameters: tuple[PsmRescoringFeatureParameter, ...],
) -> np.ndarray:
    _validate_model_feature_parameters(feature_parameters)
    return np.array(
        [
            _standardize_feature_value(
                value=_feature_row_value(row, parameter.feature_name),
                parameter=parameter,
            )
            for parameter in feature_parameters
        ],
        dtype=float,
    )


def _standardize_feature_value(
    *,
    value: float,
    parameter: PsmRescoringFeatureParameter,
) -> float:
    transformed = _transform_feature_value(value=value, transform=parameter.transform)
    return (transformed - parameter.mean) / parameter.scale


def _feature_row_value(row: PsmFeatureRow, feature_name: str) -> float:
    if feature_name not in PsmFeatureRow.model_fields:
        raise ValueError(f"unsupported_rescoring_feature:{feature_name}")
    return float(getattr(row, feature_name))


def _validate_model_feature_parameters(
    feature_parameters: tuple[PsmRescoringFeatureParameter, ...],
) -> None:
    if not feature_parameters:
        raise ValueError("rescoring model must define feature parameters")
    feature_names = tuple(parameter.feature_name for parameter in feature_parameters)
    if len(set(feature_names)) != len(feature_names):
        raise ValueError("rescoring model feature parameters must be unique")
    supported = {feature_name for feature_name, _transform in _FEATURE_SPECIFICATIONS}
    unexpected = tuple(
        feature_name for feature_name in feature_names if feature_name not in supported
    )
    if unexpected:
        raise ValueError(
            "rescoring model feature parameters must use supported PSM features"
        )


def _fit_logistic_parameters(
    feature_matrix: np.ndarray,
    labels: np.ndarray,
    *,
    regularization_strength: float,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, int, float]:
    sample_count, feature_count = feature_matrix.shape
    parameters = np.zeros(feature_count + 1, dtype=float)
    target_count = max(float(np.sum(labels == 1.0)), 1.0)
    decoy_count = max(float(np.sum(labels == 0.0)), 1.0)
    sample_weights = np.where(
        labels == 1.0,
        sample_count / (2.0 * target_count),
        sample_count / (2.0 * decoy_count),
    )
    augmented = np.column_stack([np.ones(sample_count, dtype=float), feature_matrix])
    penalty = np.diag(
        np.concatenate(([0.0], np.full(feature_count, regularization_strength)))
    )
    convergence_delta = float("inf")

    for iteration in range(1, max_iterations + 1):
        linear = augmented @ parameters
        probabilities = _sigmoid(linear)
        residual = (probabilities - labels) * sample_weights
        gradient = (augmented.T @ residual) / sample_count + penalty @ parameters
        curvature = probabilities * (1.0 - probabilities) * sample_weights
        hessian = (augmented.T * curvature) @ augmented / sample_count + penalty
        step = np.linalg.lstsq(hessian, gradient, rcond=None)[0]
        parameters -= step
        convergence_delta = float(np.linalg.norm(step))
        if convergence_delta <= tolerance:
            return parameters, iteration, convergence_delta
    return parameters, max_iterations, convergence_delta


def _rescored_q_values(
    *,
    feature_table: tuple[PsmFeatureRow, ...],
    rescored_scores: np.ndarray,
) -> dict[str, float]:
    ranked = sorted(
        zip(feature_table, rescored_scores, strict=True),
        key=lambda pair: (-float(pair[1]), pair[0].psm_id),
    )
    cumulative_targets = 0
    cumulative_decoys = 0
    raw_values_by_id: dict[str, float] = {}
    for row, _score in ranked:
        if row.target_decoy_label is TargetDecoyLabel.DECOY:
            cumulative_decoys += 1
        else:
            cumulative_targets += 1
        raw_values_by_id[row.psm_id] = min(
            cumulative_decoys / max(cumulative_targets, 1),
            1.0,
        )
    running_min = 1.0
    monotonic_values_by_id: dict[str, float] = {}
    for row, _score in reversed(ranked):
        running_min = min(running_min, raw_values_by_id[row.psm_id])
        monotonic_values_by_id[row.psm_id] = running_min
    return monotonic_values_by_id


def _rank_map(
    pairs: tuple[tuple[str, float], ...] | object,
    *,
    higher_better: bool,
) -> dict[str, int]:
    ranked = sorted(
        tuple(pairs),
        key=lambda pair: ((-pair[1]) if higher_better else pair[1], pair[0]),
    )
    return {psm_id: rank for rank, (psm_id, _score) in enumerate(ranked, start=1)}


def _binary_label(label: TargetDecoyLabel) -> float:
    if label is TargetDecoyLabel.TARGET:
        return 1.0
    if label is TargetDecoyLabel.DECOY:
        return 0.0
    return -1.0


def _transform_feature_value(*, value: float, transform: FeatureTransform) -> float:
    if transform == "absolute":
        return abs(value)
    return value


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _logit(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    return np.log(clipped / (1.0 - clipped))


def _binary_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    target_scores = scores[labels == 1.0]
    decoy_scores = scores[labels == 0.0]
    if len(target_scores) == 0 or len(decoy_scores) == 0:
        return 0.5
    wins = 0.0
    total = float(len(target_scores) * len(decoy_scores))
    for target_score in target_scores:
        for decoy_score in decoy_scores:
            if target_score > decoy_score:
                wins += 1.0
            elif target_score == decoy_score:
                wins += 0.5
    return wins / total


def _rescoring_payload(
    *,
    model: PsmRescoringModel,
    entries: tuple[PsmRescoringEntry, ...],
) -> bytes:
    payload = {
        "model": model.to_dict(),
        "entries": [entry.to_dict() for entry in entries],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
