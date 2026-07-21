---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

The compatibility layer should add negligible work beyond Python import resolution and function forwarding. Computational cost, concurrency, network latency, provider throughput, artifact volume, and memory pressure are properties of the canonical Runtime path reached through the bridge.

## Measure the complete route

Compare the historical and canonical entrypoints with the same environment, provider, request, inputs, and output destination:

```bash
time agentic-proteins --help
time bijux-proteomics-runtime --help
```

For real workflows, compare Runtime telemetry and artifacts rather than extrapolating from command startup. Preserve the same provider selection and cache state; otherwise provider or model-loading variance will dominate any forwarding cost.

Useful comparisons include:

| Signal | Interpretation |
| --- | --- |
| import or CLI startup delta | compatibility-module and environment overhead |
| identical provider selection | proof that the bridge did not alter routing |
| identical run state and artifacts | proof that execution semantics stayed canonical |
| request throughput and queue latency | Runtime or hosting behavior |
| model load time and accelerator use | provider implementation and hardware behavior |
| serialized artifact size | Runtime workflow and result shape |

## Scaling rules

Scale Runtime workers, provider capacity, storage, and queues. Adding bridge replicas changes only how many legacy callers can reach the same Runtime behavior; it does not create a distinct scaling strategy.

Avoid bridge-local memoization or caching. It can make a legacy call appear faster while producing a behavior difference that canonical callers cannot observe or invalidate. Shared caching belongs with the canonical operation and must retain the same keys, provenance, and invalidation rules for both paths.

Avoid importing broad compatibility namespaces in latency-sensitive startup code when a canonical narrow import is available. The durable optimization is migration to the direct owner, which removes an import layer and makes dependencies easier to profile.

## Escalating a regression

First reproduce the workload through both entrypoints. If only the historical path regresses, inspect forwarding topology, import cycles, and compatibility aliases. If both paths regress, investigate Runtime, the selected provider, artifact storage, or the host environment. Fix the canonical owner and verify the bridge again; do not compensate with package-local execution logic.

Performance work is complete when the same workload produces equivalent semantics through both paths and any remaining material cost has one canonical owner with measurable operating signals.
