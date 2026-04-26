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

If someone opens only this page, they should be able to route a repository
question immediately: does the rule live in maintainer helper code, in the Make
surface, or in GitHub automation?

```mermaid
flowchart LR
    reader["reader question<br/>which repository-health layer owns this rule?"]
    dev["bijux-proteomics-dev<br/>helper code and policy checks"]
    makes["makes<br/>shared command surfaces"]
    workflows["gh-workflows<br/>GitHub Actions contracts"]
    packages["product package handbooks<br/>owned user-facing behavior"]
    health["repository health<br/>release, docs, quality, automation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class reader page;
    class dev,makes,workflows,health positive;
    class packages caution;
    reader --> health
    health --> dev
    health --> makes
    health --> workflows
    health -.hands product behavior back to.-> packages
```

## Start Here

- use [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/) when the concern
  is helper code, schema drift, docs integrity, release support, or policy
  enforcement
- use [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/) when the concern starts from a shared command,
  package dispatch path, or CI target family
- use [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/) when the issue starts from a
  GitHub event, failed job tree, or publication trigger

## Pages In This Handbook

- [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/)
- [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/)
- [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/)

## Use This Handbook When

- the question is about repository automation, verification, release support,
  docs integrity, or workflow fan-out
- you need to know which shared surface owns a repository-health rule
- the answer should stay above one product package boundary

## Move On When

- the real question is about runtime, evidence, scoring, or lab behavior inside
  one product package
- you already know the issue belongs to one package API, CLI, or schema
- you are trying to understand product semantics rather than repository health

## What This Handbook Clarifies

- which repository-health questions belong to helper code, Make routing, or
  workflow automation
- where release, docs integrity, and policy enforcement live above package
  level
- when the correct move is to leave maintainer docs and hand the question back
  to a product package handbook

## Choose A Section

- use [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/) when the concern is
  helper code, schema drift, release support, or repository-health checks
- use [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/) when the concern is a shared command surface,
  package dispatch, or CI target family
- use [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/) when the concern is GitHub Actions
  triggers, job trees, or docs and release publication

## Concrete Anchors

- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/` for maintainer
  helper code
- `Makefile` and `makes/` for shared command routing
- `.github/workflows/` for GitHub-triggered verification and publication
  automation
- `docs/08-bijux-proteomics-maintain/` for the maintainer handbook tree this
  page is routing through

## Reader Takeaway

This handbook should make repository-health work explicit and reviewable. It is
not a shadow product layer, and it should send readers back to the product
package docs as soon as the question becomes user-facing behavior.
