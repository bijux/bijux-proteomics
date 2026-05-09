---
title: Cross-Package Ownership
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Cross-Package Ownership

This matrix answers one question fast: if an artifact, import, or claim crosses
package boundaries, who owns it and who is allowed to consume it.

## Package Matrix

| Package | Durable role | Allowed outbound imports | Forbidden outbound imports | Owned handoff classes |
| --- | --- | --- | --- | --- |
| `bijux-proteomics-foundation` | shared contracts, identifiers, deterministic serialization | none | core, runtime, intelligence, knowledge, lab, agentic, dev | `foundation-contract` |
| `bijux-proteomics-core` | benchmark assets, durable scientific contracts, workflow requests | foundation, runtime, intelligence, lab | knowledge, agentic, dev | `benchmark-asset-bundle` |
| `bijux-proteomics-runtime` | execution, provider binding, replay, operator entrypoints | foundation, core, intelligence | knowledge, lab, agentic, dev | `runtime-run-bundle` |
| `bijux-proteomics-knowledge` | scientific memory, provenance, contradiction handling, review state | foundation | core, runtime, intelligence, lab, agentic, dev | `scientific-review-bundle` |
| `bijux-proteomics-intelligence` | recommendation posture, ranking sensitivity, refusal behavior | foundation, core, knowledge | runtime, lab, agentic, dev | `recommendation-record` |
| `bijux-proteomics-lab` | assay consequence planning, readiness, observed outcomes | foundation, core, knowledge, intelligence | runtime, agentic, dev | `lab-consequence-record` |
| `agentic-proteins` | legacy compatibility bridge for runtime entrypoints and imports | core, intelligence, runtime | foundation, knowledge, lab, dev | none |
| `bijux-proteomics-dev` | maintainer automation, docs checks, release governance | foundation, core, runtime, intelligence, knowledge, lab | agentic | none |

## Handoff Classes

| Handoff class | Owner | Producers | Consumers | Typical examples |
| --- | --- | --- | --- | --- |
| `foundation-contract` | `bijux-proteomics-foundation` | foundation | core, runtime, knowledge, intelligence, lab | `DocumentSchema`, `JsonModel`, `ProgramId` |
| `benchmark-asset-bundle` | `bijux-proteomics-core` | core | runtime, knowledge, intelligence, lab | flagship benchmark manifest, challenge corpus package, workflow execution request |
| `runtime-run-bundle` | `bijux-proteomics-runtime` | runtime | knowledge, intelligence, lab | run manifest, artifact ledger, review output bundle |
| `scientific-review-bundle` | `bijux-proteomics-knowledge` | knowledge | intelligence, lab | evidence bundle, contradiction ledger, knowledge review packet |
| `recommendation-record` | `bijux-proteomics-intelligence` | intelligence | lab | ranking brief, recommendation stance, refusal explanation |
| `lab-consequence-record` | `bijux-proteomics-lab` | lab | knowledge, intelligence | assay plan, lab handoff, observed outcome record |

## Boundary Rules

- When an import direction is not listed as allowed here, treat it as a
  release-blocking boundary leak.
- When an artifact class is not listed here, the owner has not yet been stated
  clearly enough for cross-package publication.
- When `agentic-proteins` needs new logic, move the logic into the canonical
  owner first and keep the bridge thin.
- When root docs or release language describe behavior stronger than the owning
  package tests can prove, narrow the wording instead of widening root prose.

## First Proof Check

- `configs/package-governance/repository-product-shape.toml`
- `configs/package-governance/package-dependency-policy.toml`
- `packages/*/README.md`
- `packages/*/src/*/__init__.py`

## Design Pressure

The repository gets confusing when dependency direction, artifact ownership,
and public wording each tell a slightly different story. This matrix exists so
those three surfaces can be reviewed together.
