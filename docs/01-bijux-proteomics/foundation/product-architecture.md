---
title: Product Architecture
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Product Architecture

`bijux-proteomics` should read like one bounded product with several owners,
not like seven adjacent handbooks that only coincide in one repository. The
product promise is simple: start from benchmark-backed proteomics inputs, run a
bounded execution path, review the result scientifically, decide what posture
is justified, and only then decide whether lab follow-up is warranted.

The package split exists because those steps do not own the same truth. Shared
contracts, scientific meaning, runtime execution, evidence review,
recommendation posture, and lab consequence must stay explicit enough that a
skeptical reviewer can point to one owner for each move.

What is stronger now is the substance inside that chain. The repository has
deeper core scientific surfaces, stronger public benchmark packaging, more
concrete runtime rerun proof, clearer grounding and recommendation routes, and
more visible lab consequence than the earlier docs suggested. The architecture
page should make that product depth legible instead of sounding like a neutral
package inventory.

The architecture is therefore not only a dependency map. It is the shortest
end-to-end explanation of how this repository turns proteomics material into a
bounded scientific sentence. If any hop in that chain weakens, the public
language must narrow even when the upstream code still looks sophisticated.

## Lifecycle

| Stage | Owner | What the owner contributes | Primary surface |
| --- | --- | --- | --- |
| Shared contracts and identifiers | `bijux-proteomics-foundation` | schema compatibility, identifiers, deterministic serialization | `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation` |
| Benchmark asset intake and domain contracts | `bijux-proteomics-core` | benchmark asset packages, scientific contracts, runtime-agnostic workflow requests | `packages/bijux-proteomics-core/benchmark-assets` |
| Runtime execution and replay | `bijux-proteomics-runtime` | provider binding, reproducible runs, replay bundles, operator entrypoints | `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime` |
| Scientific review and evidence memory | `bijux-proteomics-knowledge` | grounded evidence memory, contradiction handling, review state | `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` |
| Recommendation posture and refusal logic | `bijux-proteomics-intelligence` | ranking, recommendation stance, refusal explanations | `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence` |
| Lab consequence and observed outcomes | `bijux-proteomics-lab` | assay planning, readiness, handoff honesty, observed-outcome loop | `packages/bijux-proteomics-lab/src/bijux_proteomics_lab` |

Two repository surfaces sit beside that chain rather than inside it:

- `agentic-proteins` preserves legacy runtime imports and entrypoints while
  callers migrate to canonical runtime ownership.
- `bijux-proteomics-dev` owns repository-health automation, docs integrity, and
  release governance.

## What Became Deeper Since The Earlier Handbooks

- core now carries visibly broader biological and chemical work instead of
  stopping at generic workflow contracts
- runtime now exposes stronger replay, rerun, import, and operator-facing proof
  surfaces instead of leaving reproducibility implicit
- knowledge and intelligence now carry more exact grounding, contradiction,
  challenge, confidence, and downgrade routes
- lab now contributes a clearer requested-versus-observed outcome loop instead
  of ending at soft next-step language

## What The Architecture Protects

- core can grow broader scientific logic without silently taking over runtime,
  recommendation, or lab ownership
- runtime can become more reproducible without rewriting scientific truth
- knowledge and intelligence can challenge workflow claims without hiding the
  underlying benchmark and execution surfaces
- lab can narrow public language when downstream burden remains weaker than
  upstream signal

## Cross-Package Rules

- `bijux-proteomics-foundation` supplies shared contracts and does not grow
  product behavior.
- `bijux-proteomics-core` owns benchmark-backed domain meaning and workflow
  request shapes, not runtime orchestration.
- `bijux-proteomics-runtime` owns execution control and replay, not scientific
  truth or recommendation posture.
- `bijux-proteomics-knowledge` owns evidence memory and review state, not
  ranking or assay planning.
- `bijux-proteomics-intelligence` owns recommendation strength and refusal
  logic, not evidence storage or lab execution.
- `bijux-proteomics-lab` owns assay consequence, readiness, and observed
  outcomes, not runtime control.
- `agentic-proteins` stays a compatibility bridge and must not regain new
  scientific or runtime source-of-truth logic.

## Reader Routes

- Start with [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
  when the question is which package should own a change or handoff.
- Start with [Current capability limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)
  when the question is what the repository still refuses to claim.
- Start with [Release readiness matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/)
  when the question is whether public wording currently outruns the evidence.

## Strongest Product Proof Route

- benchmark-backed scientific claim from core
- runtime lane and rerun boundary from runtime
- grounding and contradiction pressure from knowledge
- recommendation posture from intelligence
- downstream consequence from lab

If one of those hops is weak, the public sentence must narrow even when the
other hops look strong.

## What This Page Prevents

- benchmark-backed scientific depth being mistaken for blanket release
  readiness
- runtime rerun realism being mistaken for scientific transfer proof
- strong analytical judgment being mistaken for free downstream lab consequence
- package-local excellence being mistaken for a coherent end-to-end product

## First Proof Check

- `configs/package-governance/repository-product-shape.toml`
- `configs/package-governance/package-dependency-policy.toml`
- package README ownership sections and the handbooks they point to

## Design Pressure

The common failure is to describe all packages accurately in isolation while
still making the user reconstruct the end-to-end product for themselves. This
page exists to remove that reconstruction tax.
