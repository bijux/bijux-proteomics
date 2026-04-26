---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section explains which imports, files, outputs, and configuration shapes in `bijux-proteomics-intelligence` are safe to depend on and which ones are only internal machinery.

For many readers this page is the contract page that matters most. If a workflow, downstream package, or reviewer wants to rely on intelligence output, this section should make it obvious which surfaces are deliberate and which ones would be a mistake to hard-code against.

## Visual Summary

```mermaid
flowchart LR
    consumer["consumer question<br/>what can I safely rely on?"]
    imports["public imports<br/>briefs, candidates, policies, evaluators"]
    artifacts["decision artifacts<br/>briefs, reports, outcomes, serialization"]
    configs["configuration and schema shapes"]
    page["Interfaces landing page<br/>real contract surfaces"]
    callers["caller workflows"]
    reviews["compatibility review"]
    examples["examples and entrypoints"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    consumer --> page
    imports --> page
    artifacts --> page
    configs --> page
    page --> callers
    page --> reviews
    page --> examples
    class page page;
    class consumer action;
    class imports,artifacts,configs positive;
    class callers,reviews,examples anchor;
```

## Pages in This Section

- [CLI Surface](cli-surface.md)
- [API Surface](api-surface.md)
- [Configuration Surface](configuration-surface.md)
- [Data Contracts](data-contracts.md)
- [Artifact Contracts](artifact-contracts.md)
- [Entrypoints and Examples](entrypoints-and-examples.md)
- [Operator Workflows](operator-workflows.md)
- [Public Imports](public-imports.md)
- [Compatibility Commitments](compatibility-commitments.md)

## Start Here

Read this section first when you need to know whether a downstream caller may safely import a type, parse an artifact, or expect a recommendation output to keep the same shape. `bijux-proteomics-intelligence` exposes decision-facing surfaces, so weak contract wording here quickly turns into brittle downstream code.

## Read Across the Package

- [Foundation](../foundation/index.md) when you need the package boundary and ownership story first
- [Architecture](../architecture/index.md) when the question becomes structural, modular, or execution-oriented
- [Operations](../operations/index.md) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](../quality/index.md) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `src/bijux_proteomics_intelligence/__init__.py` for the public import surface
- `src/bijux_proteomics_intelligence/briefs.py` and `src/bijux_proteomics_intelligence/outcomes.py` for decision-facing outputs
- `src/bijux_proteomics_intelligence/evaluators.py` and `src/bijux_proteomics_intelligence/policies.py` for callable contract pressure
- `src/bijux_proteomics_intelligence/serialization.py` and `src/bijux_proteomics_intelligence/report/` for file and artifact shapes

## Use This Page When

- you need the public import, artifact, or configuration surface for intelligence outputs
- you are deciding whether a caller can safely depend on a recommendation, brief, report, or serialized structure
- you want to separate intentional contracts from incidental module visibility

## Do Not Use This Section When

- you are trying to understand why ranking and evaluation logic is split across modules
- you are debugging workflow steps, validation commands, or release procedure
- you are asking whether the current proof surface is strong enough for a risky change

## When To Leave This Section

Callers often start in interfaces and then discover they really need one of the adjacent sections. Move to [Architecture](../architecture/index.md) when an exposed surface raises a structural question about candidate state, policies, or evaluators. Move to [Operations](../operations/index.md) when the contract question becomes procedural, such as how a maintainer validates or ships a changed artifact. Move to [Quality](../quality/index.md) when the real question is whether the contract is sufficiently defended by tests and review.

## Reader Takeaway

Treat this section as the contract map for `bijux-proteomics-intelligence`. If a surface cannot be traced to a documented import, artifact, configuration shape, example, and test-backed expectation, readers should assume it is not yet a stable dependency boundary.
