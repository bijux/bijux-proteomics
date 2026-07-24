---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

Foundation operations are local, deterministic transformations. Their cost follows payload size, nesting, key ordering, model validation, and migration-path length—not network concurrency or worker count.

## Cost model

| Operation | Material work | Scaling pressure |
| --- | --- | --- |
| `to_canonical_json` | normalize values, order mappings, materialize compact JSON | deeply nested or large in-memory documents |
| `hash_payload` | canonicalize the full mapping and hash its encoded bytes | repeated hashing of unchanged large payloads |
| `hash_model` | convert the model, canonicalize, and hash | model size plus serialization cost |
| `flatten_tsv_mapping` | recursively flatten nested mappings | wide documents and large embedded lists |
| Pydantic model validation | validate fields and construct typed values | high record counts and complex nested models |
| migration resolution | walk registered version edges and apply each transform | long chains or transforms that copy large payloads |

Canonical JSON and hashes are intentionally value-stable. Do not replace sorted serialization with a faster order-dependent form, use a process-random hash, or skip validation on one execution path. Such changes trade durable identity for a benchmark result.

## Benchmark the representative artifact

The governed performance surface exercises a nested document with 160 records, measurement fields, annotations, provenance, and artifact locators. It protects a realistic medium document shape; it is not a universal latency guarantee.

From a source checkout:

```bash
python -m pytest \
  packages/bijux-proteomics-foundation/tests/performance/test_hashing_and_serialization_benchmark_surface.py
```

Compare like with like: same Python version, payload, schema, hash policy, and benchmark configuration. Record payload size and record count alongside timing so a faster result is not merely a smaller fixture.

## Safe optimization order

1. Avoid canonicalizing or hashing the same immutable payload repeatedly within one owned workflow.
2. Keep large binary or tabular assets outside JSON documents and store governed references plus fingerprints.
3. Batch at the consuming workflow boundary when records can remain independently reviewable.
4. Profile normalization, validation, serialization, and hashing separately.
5. Optimize the shared implementation only after tests prove identical bytes, digests, exceptions, and migration outcomes.

Caching belongs to the consuming package because only that owner knows artifact lifetime and invalidation. Cache keys should include the canonical fingerprint and any schema or policy identity that changes meaning.

## Memory and migration limits

Canonical rendering and migration materialize Python objects and output strings; they are not streaming interfaces. For very large datasets, persist chunked domain artifacts and use Foundation contracts for manifests, partitions, lineage, and integrity. A migration that requires rewriting a large corpus should be an explicit operational job with resumability and audit artifacts owned outside Foundation.
