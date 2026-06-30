---
title: Repository Scope
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Repository Scope

The root should stay narrow. It exists to hold shared docs structure,
repository-wide validation and release framing, tracked API artifacts, and other
assets that genuinely cross package boundaries. It should not become a backup
owner for product behavior.

That narrowness is more important now because the product beneath it is
stronger. Once core, runtime, knowledge, intelligence, and lab all carry real
owner logic, the root becomes dangerous if it starts absorbing convenience
behavior just because several packages touch the same release sentence.

## Scope Model

```mermaid
flowchart TB
    root["root surface"]
    docs["docs and handbook routing"]
    apis["tracked contract artifacts"]
    process["make, workflow, and release coordination"]
    product["product behavior"]

    root --> docs
    root --> apis
    root --> process
    product -. stays out of root .-> root
```

This page should help a reviewer reject the common excuse that something belongs at the root because several packages touch it. Shared touch does not equal shared ownership.

## Root Scope

- handbook structure and cross-package routing under `docs/`
- tracked contract artifacts under `apis/`
- repository-wide command, workflow, and release coordination under
  `Makefile`, `makes/`, and `.github/workflows/`
- workspace metadata and root governance files when they affect several
  packages together

## Why Narrow Root Scope Protects The Product

- it keeps repository-wide wording from mutating into hidden product logic
- it forces biology, runtime, evidence, recommendation, and consequence
  behavior back into the packages that actually prove them
- it keeps shared release framing honest when one package grows faster than the
  others

## Out Of Scope

- runtime execution behavior
- evidence, decision, or lab semantics
- package-local contracts that happen to be reused elsewhere

## Failure Mode To Reject

A root change that adds product behavior because it is easier to wire once at
the top is usually the wrong change. Shared convenience is not the same thing
as shared ownership.

## Strongest Reader Route

- use this page when a change proposal claims root ownership because it spans
  several packages
- then open
  [Ownership Model](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/ownership-model/)
  or
  [Cross-Package Ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
  to decide whether the scope is truly shared or only widely consumed

## First Proof Check

- root files only when the rule truly spans several packages
- otherwise the owning package handbook, code, and tests

## Design Pressure

The common drift is to broaden root scope one convenience change at a time until product behavior has no clean owner anymore.
