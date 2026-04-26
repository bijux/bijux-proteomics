---
title: Maintainer Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Maintainer Handbook

`bijux-proteomics-maintain` is the handbook root for repository-owned
maintenance work.

This section exists so repository health stays inspectable. Quality gates,
schema drift checks, docs integrity checks, release support, and workflow
contracts should be readable from checked-in docs instead of being rediscovered
through CI logs and shell glue.

This handbook is for work that sits above one product package boundary. It
should help a maintainer answer a repository-health question quickly without
mistaking shared automation for product behavior.

```mermaid
flowchart LR
    handbook["Maintainer handbook"]
    dev["bijux-proteomics-dev<br/>helper code and policy checks"]
    makes["makes<br/>shared command surfaces"]
    workflows["gh-workflows<br/>GitHub Actions contracts"]
    packages["product package handbooks<br/>owned user-facing behavior"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class handbook page;
    class dev,makes,workflows positive;
    class packages caution;
    handbook --> dev
    handbook --> makes
    handbook --> workflows
    handbook -.hands product behavior back to.-> packages
```

## Sections In This Handbook

- [bijux-proteomics-dev](bijux-proteomics-dev/index.md)
- [makes](makes/index.md)
- [gh-workflows](gh-workflows/index.md)

## Use This Handbook When

- the question is about repository automation, verification, release support,
  docs integrity, or workflow fan-out
- you need to know which shared surface owns a repository-health rule
- the answer should stay above one product package boundary

## Do Not Start Here When

- the real question is about runtime, evidence, scoring, or lab behavior inside
  one product package
- you already know the issue belongs to one package API, CLI, or schema
- you are trying to understand product semantics rather than repository health

## Choose The Next Section By Question

- open [bijux-proteomics-dev](bijux-proteomics-dev/index.md) when the concern is
  helper code, schema drift, release support, or repository-health checks
- open [makes](makes/index.md) when the concern is a shared command surface,
  package dispatch, or CI target family
- open [gh-workflows](gh-workflows/index.md) when the concern is GitHub Actions
  triggers, job trees, or docs and release publication

## Reader Takeaway

This handbook should make repository-health work explicit and reviewable. It is
not a shadow product layer, and it should send readers back to the product
package docs as soon as the question becomes user-facing behavior.

## Purpose

This page gives maintainers a stable starting point for repository-health
documentation.

## Stability

Keep it aligned with the section roots that actually exist under
`docs/bijux-proteomics-maintain/`.
