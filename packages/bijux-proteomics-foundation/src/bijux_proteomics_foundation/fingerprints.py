# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed fingerprint records for datasets and execution artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.hashing import (
    StableHashPolicy,
    default_hash_policy,
    hash_payload,
)
from bijux_proteomics_foundation.ordering import stable_order_strings
from bijux_proteomics_foundation.json_models import JsonModel


class FingerprintScope(StrEnum):
    """Canonical fingerprint scopes shared across packages."""

    DATASET = "dataset"
    PARAMETER_SET = "parameter_set"
    RUN_CONTEXT = "run_context"
    BENCHMARK_MANIFEST = "benchmark_manifest"
    ARTIFACT_BUNDLE = "artifact_bundle"


class FingerprintRecord(JsonModel):
    """One named fingerprint built under a stable policy."""

    model_config = ConfigDict(extra="forbid")

    scope: FingerprintScope
    fingerprint: str = Field(..., min_length=64, max_length=64)
    hash_policy_id: str = Field(..., min_length=1)
    subject_id: str | None = None
    input_labels: tuple[str, ...] = Field(default_factory=tuple)


def build_fingerprint_record(
    scope: FingerprintScope,
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
    policy: StableHashPolicy | None = None,
) -> FingerprintRecord:
    """Build one typed fingerprint record for a canonical payload."""
    active_policy = policy or default_hash_policy()
    return FingerprintRecord(
        scope=scope,
        fingerprint=hash_payload(payload, policy=active_policy),
        hash_policy_id=active_policy.policy_id,
        subject_id=subject_id,
        input_labels=stable_order_strings(input_labels),
    )


def build_dataset_fingerprint(
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
) -> FingerprintRecord:
    """Build a dataset fingerprint."""
    return build_fingerprint_record(
        FingerprintScope.DATASET,
        payload,
        subject_id=subject_id,
        input_labels=input_labels,
    )


def build_parameter_set_fingerprint(
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
) -> FingerprintRecord:
    """Build a parameter-set fingerprint."""
    return build_fingerprint_record(
        FingerprintScope.PARAMETER_SET,
        payload,
        subject_id=subject_id,
        input_labels=input_labels,
    )


def build_run_context_fingerprint(
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
) -> FingerprintRecord:
    """Build a run-context fingerprint."""
    return build_fingerprint_record(
        FingerprintScope.RUN_CONTEXT,
        payload,
        subject_id=subject_id,
        input_labels=input_labels,
    )


def build_benchmark_manifest_fingerprint(
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
) -> FingerprintRecord:
    """Build a benchmark-manifest fingerprint."""
    return build_fingerprint_record(
        FingerprintScope.BENCHMARK_MANIFEST,
        payload,
        subject_id=subject_id,
        input_labels=input_labels,
    )


def build_artifact_bundle_fingerprint(
    payload: dict[str, Any],
    *,
    subject_id: str | None = None,
    input_labels: tuple[str, ...] = (),
) -> FingerprintRecord:
    """Build an artifact-bundle fingerprint."""
    return build_fingerprint_record(
        FingerprintScope.ARTIFACT_BUNDLE,
        payload,
        subject_id=subject_id,
        input_labels=input_labels,
    )
