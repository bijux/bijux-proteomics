---
title: Testing and Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-04
---

# Testing and Validation

Validation in `bijux-proteomics` is layered: packages protect their own behavior,
while the repository protects the seams between packages, schemas, docs, and
release conventions.

Trust has to be local before it can be global. Each package proves its own
promises first. The repository then proves that the packages still fit
together honestly.

## Layers Of Proof

```mermaid
flowchart TB
    package["package-local tests<br/>unit, integration, e2e, invariants"]
    seams["cross-package checks<br/>schema drift, packaging, docs fit"]
    ci["repository CI<br/>whole-workspace confidence"]
    trust["credible release confidence"]

    package --> seams --> ci --> trust
```

## Validation Layers

- package-local unit, integration, e2e, and invariant suites
- API contract checks in `apis/*/v1` enforced by `make api`, `make api-freeze`, and `make openapi-drift`
- schema drift and packaging checks in `bijux-proteomics-dev`
- repository CI workflows under `.github/workflows/`

## Validation Rule

A prose promise is incomplete until either package tests or repository tooling
can detect its drift.

Docs can explain why a check matters. Docs cannot substitute for the check.
