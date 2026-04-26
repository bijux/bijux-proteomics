---
title: bijux-proteomics-foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-foundation

`bijux-proteomics-foundation` is the shared schema and serialization
package in `bijux-proteomics`. Start here when the question is about
canonical payload shape, version compatibility helpers, identity
primitives, or deterministic serialization contracts used across the
package family.

This package stabilizes shared meaning so the higher packages can disagree
about policy or workflow without disagreeing about what a payload is.

This page shows that the package is not “misc shared utilities.” It is the
layer that keeps identifiers, schema metadata, migrations, errors, and
deterministic serialization compatible enough for the rest of the family to
exchange meaning safely.

## Start Here

```mermaid
flowchart LR
    reader["reader question<br/>what keeps payload meaning stable across packages?"]
    identifiers["ids.py and migrations.py<br/>stable identifiers and version bridges"]
    schema["schema.py and errors.py<br/>document metadata and shared failure language"]
    serialization["serialization.py<br/>canonical payloads and fingerprints"]
    dependents["core, knowledge, intelligence,<br/>lab, and runtime consume the same meaning"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class identifiers,schema,serialization,dependents positive;
    reader --> identifiers
    reader --> schema
    reader --> serialization
    identifiers --> dependents
    schema --> dependents
    serialization --> dependents
```

## Open This Section When

- you need the package entrypoint for schema and payload contracts
- you are checking identifiers, migrations, or serialization guarantees
- you want the shortest route into shared cross-package primitives

## Open Another Package When

- the real issue is already about program rules, evidence state, ranking
  policy, lab planning, or runtime execution
- you need downstream package behavior rather than shared payload meaning
- you are treating this package as a generic utility layer instead of as a
  contract layer

## Package Sections

- [Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/)
- [Quality](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/quality/)

## Cross-Package Handoffs

- open [bijux-proteomics-core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) when the concern becomes program or lifecycle behavior
- open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) when the concern becomes execution or replay
- stay here when the real question is whether shared payload meaning changed

## What This Package Clarifies

- which identifier and schema rules are shared by the whole package family
- how deterministic serialization is kept compatible enough for review and
  interchange
- where a migration or payload-shape change should be judged before it ripples
  downstream

## Concrete Anchors

- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/ids.py`
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/migrations.py`
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/schema.py`
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation/serialization.py`
- `packages/bijux-proteomics-foundation/tests` for compatibility and canonical
  payload proof

## Bottom Line

Open this page when the unresolved question is whether proteomics packages still
mean the same thing when they exchange payloads. If the answer depends on
policy, workflow, or execution rather than on shared meaning, another package
owns the decision.
