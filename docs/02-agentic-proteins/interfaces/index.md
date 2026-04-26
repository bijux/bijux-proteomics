---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section explains which commands, APIs, imports, schemas, and artifacts
`agentic-proteins` still preserves as compatibility surfaces.

These pages help a caller separate migration-safe preserved entrypoints from
incidental visibility. The point is to show what still forwards deliberately
and what should now send readers to `bijux-proteomics-runtime` instead.

This section shows whether they are still depending on a legacy
surface, what it forwards to, and what kind of review is required before that
surface changes.

## Pages In This Section

- [CLI Surface](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/compatibility-commitments/)

## Open This Section When

- you need to know whether a legacy CLI, import, schema, or artifact surface is
  still preserved
- you are checking whether a change would break migration-safe caller behavior
- you need the compatibility contract before updating callers

## Open Another Section When

- the real question is about the canonical runtime interface rather than the
  preserved legacy alias
- you are designing a new public surface instead of preserving an old one
- the concern is structural or operational rather than caller-facing

## Bottom Line

This section is about what still forwards safely, not about where new
dependencies should begin. If a caller can open the canonical runtime
surface, that is the preferred long-term answer.

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/) when you need the package boundary and ownership story first
- [Architecture](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/) when the question becomes structural, modular, or execution-oriented
- [Operations](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/) when the question becomes procedural, environmental, diagnostic, or release-oriented
- [Quality](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- CLI entrypoint in src/agentic_proteins/interfaces/cli.py
- HTTP app in src/agentic_proteins/api/app.py
- canonical API schema in apis/bijux-proteomics-runtime/v1 with compatibility mirror in apis/agentic-proteins/v1
- apis/bijux-proteomics-runtime/v1/schema.yaml (canonical) and apis/agentic-proteins/v1/schema.yaml (compatibility mirror)

## Open This Page When

- you need the public command, API, import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Decision Rule

Open this section to decide whether a caller-facing surface is explicit enough to depend on. If the surface cannot be tied back to concrete code, schemas, artifacts, examples, and tests, treat it as unstable until that evidence is visible.

## What You Can Resolve Here

- which public or operator-facing surfaces `agentic-proteins` is really asking readers to trust
- which schemas, artifacts, imports, or commands behave like contracts
- what compatibility pressure a change to this surface would create

## Review Focus

- compare commands, schemas, imports, and artifacts against the documented surface one by one
- check whether a seemingly local change actually needs compatibility review
- confirm that examples still point to real entrypoints and not to stale habits

## Limits

This page can identify the intended public surfaces of `agentic-proteins`, but real compatibility depends on code, schemas, artifacts, examples, and tests staying aligned. If those disagree, the prose is wrong or incomplete.

## Read Next

- open operations when the caller-facing question becomes procedural or environmental
- open quality when compatibility or evidence of protection becomes the real issue
- open architecture when a public-surface question reveals a deeper structural drift

