---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

Performance advice is only useful when it points to the real owner of the bottleneck.

## Operating Rules

- optimize only when schema or serialization cost is demonstrably real
- do not trade shared clarity for minor throughput gains
- prefer predictable migrations over clever fast paths that hide compatibility cost

## First Proof Check

- `src/bijux_proteomics_foundation/documents.py` and `compatibility.py`
- `src/bijux_proteomics_foundation/serialization/`
- `packages/bijux-proteomics-foundation/tests/performance/test_hashing_and_serialization_benchmark_surface.py`
- `configs/package-governance/foundation-benchmark-surfaces.toml`
