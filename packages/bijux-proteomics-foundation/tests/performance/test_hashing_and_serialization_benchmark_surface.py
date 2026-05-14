# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from typing import Any, cast

from bijux_proteomics_foundation import hash_payload, to_canonical_json


def _medium_document_payload(record_count: int = 160) -> dict[str, object]:
    records = []
    for index in range(record_count):
        records.append(
            {
                "record_id": f"record-{index:04d}",
                "group": f"group-{index % 8}",
                "measurements": {
                    "intensity": round(50_000.0 + index * 118.25, 3),
                    "score": round(0.75 + (index % 11) * 0.013, 6),
                    "retention_time_seconds": round(920.0 + index * 1.75, 3),
                    "precursor_mz": round(400.2 + index * 0.04, 4),
                    "fragment_mz": round(101.4 + index * 0.015, 4),
                    "signal_to_noise": round(12.5 + (index % 7) * 0.9, 3),
                },
                "annotations": {
                    "sequence": f"PEPTIDE{index:04d}",
                    "modifications": [
                        {"site": 3, "name": "oxidation"},
                        {"site": 7, "name": "acetylation"},
                    ],
                    "charge_states": [2, 3],
                },
                "provenance": {
                    "source_system": "instrument-export",
                    "instrument": {
                        "model": "orbitrap-exploris",
                        "run_id": f"run-{index % 4}",
                    },
                    "artifacts": [
                        {
                            "artifact_kind": "peak-list",
                            "locator": (
                                f"artifacts/imports/run-{index % 4}/"
                                f"record-{index:04d}.json"
                            ),
                        },
                        {
                            "artifact_kind": "quality-audit",
                            "locator": (
                                f"artifacts/imports/run-{index % 4}/"
                                f"record-{index:04d}.audit.json"
                            ),
                        },
                    ],
                },
                "tags": [
                    f"tag-{index % 5}",
                    f"batch-{index % 3}",
                    "benchmark-medium",
                ],
            }
        )
    return {
        "document_schema": {
            "schema_version": "1.2.0",
            "created_by": "bijux-proteomics-foundation",
            "document_kind": "benchmark_manifest",
            "package_name": "bijux-proteomics-foundation",
            "package_version": "0.0.0",
        },
        "dataset": {
            "dataset_id": "dataset-benchmark-medium",
            "records": records,
            "summary": {
                "replicate_groups": ["control", "treated"],
                "quality_thresholds": {
                    "minimum_signal_to_noise": 10.0,
                    "maximum_retention_drift_seconds": 45.0,
                },
                "review": {
                    "release_ready": True,
                    "notes": (
                        "payload mirrors the nested bundle shape used for "
                        "cross-package artifact exchange"
                    ),
                },
            },
            "notes": [
                "payload reflects medium-size durable artifact exchange",
                "hashing and canonicalization must stay deterministic under nested records",
            ],
        },
    }


def test_canonical_json_benchmark_handles_medium_document_payload(
    benchmark: Any,
) -> None:
    payload = _medium_document_payload()

    rendered = benchmark(to_canonical_json, payload)

    assert rendered.startswith("{")
    assert '"dataset_id":"dataset-benchmark-medium"' in rendered


def test_hash_payload_benchmark_handles_medium_document_payload(
    benchmark: Any,
) -> None:
    payload = _medium_document_payload()

    digest = benchmark(hash_payload, payload)

    assert len(digest) == 64


def test_medium_document_payload_stays_realistically_nested() -> None:
    payload = _medium_document_payload()
    dataset = cast(dict[str, object], payload["dataset"])
    records = cast(list[dict[str, object]], dataset["records"])
    first_record = records[0]

    assert len(records) == 160
    assert sorted(cast(dict[str, object], first_record["measurements"])) == [
        "fragment_mz",
        "intensity",
        "precursor_mz",
        "retention_time_seconds",
        "score",
        "signal_to_noise",
    ]
    annotations = cast(dict[str, object], first_record["annotations"])
    provenance = cast(dict[str, object], first_record["provenance"])
    assert len(cast(list[object], annotations["modifications"])) == 2
    assert len(cast(list[object], provenance["artifacts"])) == 2
