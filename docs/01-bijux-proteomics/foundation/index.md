---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Foundation

The foundation section explains why `bijux-proteomics` exists in this shape
before it explains how the repository is operated.

Leave this section with a durable understanding of
the package split, the ownership model, the shared vocabulary, and the change
rules that keep the repository legible over time.

This section answers one question decisively: why is this repository a
package family instead of one large proteomics codebase with blurred ownership?
If that answer still feels vague after this page, the rest of the handbook will
only inherit the same confusion.

```mermaid
flowchart LR
    reader["reader question<br/>why is proteomics split this way?"]
    split["repository split<br/>foundation, core, intelligence,<br/>knowledge, lab, runtime"]
    ownership["ownership model<br/>which package decides what"]
    language["shared language<br/>terms, docs, change rules"]
    decisions["change decisions<br/>what belongs where"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    class reader page;
    class split,ownership,language,decisions positive;
    reader --> split
    split --> ownership
    ownership --> language
    language --> decisions
```

## Start Here

- open [Platform Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/platform-overview/) for the shortest explanation
  of what the repository is trying to be
- open [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/) when the key question is which package owns
  which concern
- open [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/) when a proposed change may cross a
  package boundary
- open [Decision Rules](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-rules/) when you need the repository’s
  actual bar for changing the split

## Pages In This Section

- [Platform Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/platform-overview/)
- [Repository Scope](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/repository-scope/)
- [Workspace Layout](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workspace-layout/)
- [Package Map](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/package-map/)
- [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/)
- [Domain Language](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/domain-language/)
- [Documentation System](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/documentation-system/)
- [Change Principles](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/change-principles/)
- [Decision Rules](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-rules/)

## Open This Section When

- you need the package-family rationale before reading package-local docs
- you are deciding whether a concern belongs at the repository root or inside
  one package handbook
- you need shared vocabulary for discussing boundaries, docs, or change scope

## Open Another Section When

- the real question is already about one package’s API, runtime, evidence, or
  lab behavior
- the issue is mainly operational and you need repeatable workflows rather than
  ownership framing
- you already know the package boundary and now need code or validation detail

## What This Section Clarifies

- why the current package split exists instead of a flatter or more entangled
  repository
- how the repository distinguishes shared meaning, durable contracts, evidence
  state, ranking policy, lab planning, and execution
- which root-level rules should stay stable so the package handbooks can remain
  honest

## Concrete Anchors

- `docs/` for the root handbook structure that mirrors the package split
- `packages/` for the package-family surface this section is explaining
- `packages/bijux-proteomics-dev/` for repository-health support that should
  not be confused with product-package ownership
- `Makefile` and `makes/` for root-owned process surfaces discussed later in
  the operations section

## Bottom Line

Open the foundation section when the unresolved question is why the repository
is organized as a family of accountable packages. If the answer depends on one
package’s local behavior rather than on the split itself, this section should
hand you off quickly instead of pretending root docs own the detail.
