# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import hash_payload, to_canonical_json


def _medium_document_payload(record_count: int = 160) -> dict[str, object]:
    records = []
    for index in range(record_count):
        records.append(
            {
                "record_id": f"record-{index:04d}",
                "group": f"group-{index % 8}",
                "metrics": {
                    "score": round(0.75 + (index % 11) * 0.013, 6),
                    "retention_time_seconds": round(920.0 + index * 1.75, 3),
                    "precursor_mz": round(400.2 + index * 0.04, 4),
                },
                "tags": [f"tag-{index % 5}", f"batch-{index % 3}"],
                "provenance": {
                    "source_system": "bijux-proteomics-runtime",
                    "artifact_locator": f"artifacts/runs/run-{index % 4}/record-{index:04d}.json",
                },
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
            "notes": [
                "payload reflects medium-size durable artifact exchange",
                "hashing and canonicalization must stay deterministic under nested records",
            ],
        },
    }


def test_canonical_json_benchmark_handles_medium_document_payload(benchmark) -> None:
    payload = _medium_document_payload()

    rendered = benchmark(to_canonical_json, payload)

    assert rendered.startswith("{")
    assert '"dataset_id":"dataset-benchmark-medium"' in rendered


def test_hash_payload_benchmark_handles_medium_document_payload(benchmark) -> None:
    payload = _medium_document_payload()

    digest = benchmark(hash_payload, payload)

    assert len(digest) == 64
