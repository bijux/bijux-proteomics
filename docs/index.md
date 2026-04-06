---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-04
---

# Bijux Proteomics

`bijux-proteomics` is split on purpose. It is easier to understand, review, and
trust when ingest, retrieval, reasoning, orchestration, and runtime authority
stay separate instead of dissolving into one vague codebase.

This landing page is for orientation. A reader should be able to skim it,
decide where their question belongs, and move on without needing a meeting.

## How To Read The Site

```mermaid
flowchart LR
    start["Start with the question you have"]
    repo["Repository handbook<br/>shared rules and system fit"]
    ingest["bijux-proteomics-ingest<br/>prepare and normalize material"]
    index["bijux-proteomics-index<br/>execute retrieval and track provenance"]
    reason["bijux-proteomics-reason<br/>turn evidence into inspectable claims"]
    agent["bijux-proteomics-agent<br/>coordinate role-based work"]
    runtime["bijux-proteomics-runtime<br/>govern replay, persistence, acceptance"]
    dev["bijux-proteomics-dev<br/>maintainer-only tooling"]
    compat["compat-packages<br/>legacy names and shims"]

    start --> repo
    start --> ingest
    start --> index
    start --> reason
    start --> agent
    start --> runtime
    start --> dev
    start --> compat
```

## Start Here

- Open the [Repository Handbook](bijux-proteomics/index.md) when the question
  crosses package boundaries or touches shared repository rules.
- Open one product package when the question is about owned behavior, public
  surfaces, workflows, or proof inside that package.
- Open [bijux-proteomics-dev](bijux-proteomics-dev/index.md) only for maintainer-side
  automation, release helpers, schema drift checks, and similar repository
  health concerns.
- Open [compat-packages](compat-packages/index.md) only when a legacy name is
  part of the problem. They exist to help migration, not to compete with the
  canonical package family.
- Open one legacy package handbook under `compat-packages/` when the exact PyPI
  distribution name is part of the migration question.

## The Five Core Packages

- [`bijux-proteomics-ingest`](bijux-proteomics-ingest/index.md) is where raw
  material becomes deterministic, reviewable input.
- [`bijux-proteomics-index`](bijux-proteomics-index/index.md) is where
  retrieval becomes explicit and provenance-aware.
- [`bijux-proteomics-reason`](bijux-proteomics-reason/index.md) is where
  evidence becomes claims, checks, and inspectable reasoning traces.
- [`bijux-proteomics-agent`](bijux-proteomics-agent/index.md) is where
  role-based work is coordinated into coherent runs.
- [`bijux-proteomics-runtime`](bijux-proteomics-runtime/index.md) is where the
  system decides whether a run is acceptable, replayable, and worth keeping.

## Two Supporting Sections

- [`bijux-proteomics-dev`](bijux-proteomics-dev/index.md) owns the developer tooling and
  maintainer workflows that do not belong in a product package.
- [`compat-packages`](compat-packages/index.md) explains the legacy names that
  still exist as migration shims.

The root docs should shorten conversations, not create new documentation
ceremony.
