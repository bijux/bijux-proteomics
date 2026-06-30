---
title: Execution
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-06-30
---

# Execution

This route owns the operator and outsider question: how does a public benchmark
package become a reviewable runtime bundle without maintainer narration. Its
owner is `bijux-proteomics-runtime`, because this is where run mode, replay,
artifact integrity, and failure boundaries become concrete.

Execution is one of the places where the repository is much deeper now than
older docs implied. The runtime surface is no longer only one CLI path. It now
owns raw versus import honesty, replay and resume pressure, checked run
registries, preflight and refusal routes, artifact integrity, and runtime
bundle comparability.

## How To Read Runtime Proof

- start by separating run mode honesty from scientific meaning:
  `raw_executable` and `import_only` are runtime statements, not universal
  trust statements
- read checked bundles and comparability surfaces before assuming that one
  rerun lane authorizes broader language
- treat replay, refusal, and artifact-stability routes as part of the runtime
  claim, not as maintenance detail

## What Runtime Evidence Means Here

- a workflow family earns stronger runtime language only when its benchmark
  package, run mode, rerun kit, verification route, and refusal surfaces still
  agree
- `raw_executable` means the current strongest public route runs from raw
  inputs through reviewable runtime artifacts
- `import_only` means the strongest current route still depends on external
  engine output even if the downstream review path is honest and useful
- runtime proof is about reproducible execution and artifact integrity, not
  about rewriting scientific meaning that belongs to core, knowledge, or lab

## Start Here

- Open [Operator Rerun Journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
  when the question is how to rerun or replay one flagship workflow family from
  benchmark package to checked output.
- Open [Black-Box Benchmark Dashboard](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-benchmark-dashboard/)
  when the question is whether current workflow language survives live rerun
  evidence.
- Open [Flagship Run Registry](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/flagship-run-registry/)
  when the question is which checked runs the repository is actually using.

## What Is Materially Stronger In 0.3.8

- the runtime story now covers both raw-executable and import-backed families
  without pretending they earn the same sentence
- replay, rerun, and artifact-boundary routes are now explicit public docs
  instead of maintainer-only background knowledge
- the current runtime route now shows how benchmark assets, execution lanes,
  challenge bundles, and downstream decision pressure connect without hiding
  refusal or downgrade cases

## Runtime Evidence Surfaces

- [Benchmark Rerun Kits](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/benchmark-rerun-kits/)
- [Runtime Execution Boundary](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-execution-boundary/)
- [Black-Box Run Verification](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/black-box-run-verification/)
- [Runtime Replay Challenges](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-replay-challenges/)
- [Runtime Environment Contracts](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-environment-contracts/)
- [Runtime Artifact Stability](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-artifact-stability/)
- [Runtime Rerun Refusals](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/runtime-rerun-refusals/)
- [Raw Versus Import Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/raw-versus-import-execution/)

## Adjacent Questions

- Open [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when the question is whether the public source package itself is complete
  enough to deserve flagship attention.
- Open [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when the question is which family language survives the current run mode and
  blocker set.
- Open [Maintenance](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintenance-overview/)
  when the question becomes which release gates and validation commands must
  pass before stronger runtime language is published.

## What This Route Still Does Not Prove

- scientific truth independent of benchmark, knowledge, or lab owners
- vendor-parity claims just because one runtime lane is reproducible
- downstream assay worth just because execution can be reopened and inspected

## Boundary

This route should answer how execution works and where execution stops. It
should not quietly absorb benchmark ownership, recommendation truth, or lab
meaning just because those later surfaces consume runtime artifacts.
