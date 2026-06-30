---
title: Product Architecture
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Product Architecture

`bijux-proteomics` is one bounded product with several owners, not several
packages that only happen to sit in one repository.

The end-to-end promise is simple:

1. accept benchmark-backed proteomics evidence
2. preserve shared meaning and compatibility
3. execute a reviewable runtime lane
4. ground the resulting sentence scientifically
5. narrow or refuse the recommendation when pressure appears
6. make downstream lab burden explicit before follow-up is treated as justified

The package split exists because those six moves do not own the same truth.

## End-To-End Chain

| stage | owner | what that owner contributes | what it must not quietly take over |
| --- | --- | --- | --- |
| shared meaning | `bijux-proteomics-foundation` | identifiers, compatibility, deterministic serialization, stable cross-package contracts | scientific workflow claims, runtime control, recommendation posture |
| scientific evidence root | `bijux-proteomics-core` | benchmark assets, sequence and chemistry surfaces, spectra and mzML handling, identification, quantification, PTM and workflow contracts | runtime orchestration, final recommendation strength, assay-worth judgment |
| runtime proof | `bijux-proteomics-runtime` | rerun lanes, replay, artifact stability, refusal surfaces, operator entrypoints | benchmark ownership, scientific truth, recommendation authority |
| grounded review | `bijux-proteomics-knowledge` | claim grounding, contradiction review, literature pressure, evidence memory | runtime proof, ranking, assay planning |
| recommendation posture | `bijux-proteomics-intelligence` | downgrade logic, challenge surfaces, confidence pressure, regret review | evidence storage, benchmark ownership, lab execution |
| downstream consequence | `bijux-proteomics-lab` | planning, readiness, refusal, requested-versus-observed outcome loops, follow-up burden | scientific meaning, runtime control, evidence grounding |

Two repository-adjacent surfaces sit beside that chain:

- `agentic-proteins` preserves historical runtime compatibility
- `bijux-proteomics-dev` owns repository health, docs integrity, release
  checks, and maintainer tooling

## What Is Deeper Since v0.3.7

The product is materially stronger than the older docs implied:

- `core` now owns visibly broader biology and chemistry surfaces instead of
  thin workflow wrappers
- `runtime` now owns replay, rerun kits, artifact verification, and refusal
  routes rather than one convenient command path
- `knowledge` and `intelligence` now expose grounded contradiction, challenge,
  downgrade, and recommendation pressure explicitly
- `lab` now owns real consequence, readiness, and outcome-learning loops
  instead of generic “next step” prose

That deeper substance is exactly why the architecture page matters. More real
product depth means the boundary between owners has to become clearer, not
blurrier.

## What The Architecture Protects

- stronger scientific breadth in core does not silently turn into runtime or
  recommendation ownership
- stronger runtime proof does not silently widen scientific truth
- grounded claim support does not silently widen recommendation posture
- promising analytical posture does not silently widen downstream lab value

The architecture exists to keep those owner changes legible.

## Strongest Reader Route

Read the chain in this order when you want the shortest serious explanation:

1. [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
2. [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
3. [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
4. [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/)
5. [Lab Consequence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lab-consequence/)

If one hop weakens, the public sentence narrows there.

## First Boundary Checks

- [Cross-Package Ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
- [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)

## Boundary

This page owns the product chain and the owner split. It should not dissolve
into a package inventory once the end-to-end logic is already clear.
