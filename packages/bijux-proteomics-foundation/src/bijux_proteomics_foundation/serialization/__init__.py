# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owner paths for deterministic serialization and document primitives."""

from __future__ import annotations

from bijux_proteomics_foundation.serialization.canonicalization import (
    flatten_tsv_mapping,
    normalize_json_value,
    to_canonical_json,
)
from bijux_proteomics_foundation.serialization.documents import DocumentSchema
from bijux_proteomics_foundation.serialization.fingerprints import (
    FingerprintRecord,
    FingerprintScope,
    build_artifact_bundle_fingerprint,
    build_benchmark_manifest_fingerprint,
    build_dataset_fingerprint,
    build_fingerprint_record,
    build_parameter_set_fingerprint,
    build_run_context_fingerprint,
)
from bijux_proteomics_foundation.serialization.hashing import (
    StableHashAlgorithm,
    StableHashPolicy,
    default_hash_policy,
    hash_model,
    hash_payload,
    hash_text,
)
from bijux_proteomics_foundation.serialization.json_models import (
    JsonModel,
    fingerprint_model,
)
from bijux_proteomics_foundation.serialization.ordering import stable_order_value

__all__ = [
    "DocumentSchema",
    "FingerprintRecord",
    "FingerprintScope",
    "JsonModel",
    "StableHashAlgorithm",
    "StableHashPolicy",
    "build_artifact_bundle_fingerprint",
    "build_benchmark_manifest_fingerprint",
    "build_dataset_fingerprint",
    "build_fingerprint_record",
    "build_parameter_set_fingerprint",
    "build_run_context_fingerprint",
    "default_hash_policy",
    "fingerprint_model",
    "flatten_tsv_mapping",
    "hash_model",
    "hash_payload",
    "hash_text",
    "normalize_json_value",
    "stable_order_value",
    "to_canonical_json",
]
