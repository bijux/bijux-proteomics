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

Repository health stays inspectable here. Quality gates, schema drift checks, docs integrity checks, release support, and workflow contracts stay readable from checked-in docs instead of being rediscovered through CI logs and shell glue.

This handbook is for work that sits above one product package boundary. It
helps a maintainer answer a repository-health question quickly without
mistaking shared automation for product behavior.

This page routes one repository-health question immediately: does the rule live in maintainer helper code, the Make surface, or GitHub automation?

## Start Here

- open [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/) when the concern
  is helper code, schema drift, docs integrity, release support, or policy
  enforcement
- open [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/) when the concern starts from a shared command,
  package dispatch path, or CI target family
- open [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/) when the issue starts from a
  GitHub event, failed job tree, or publication trigger

## Pages In This Handbook

- [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/)
- [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/)
- [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/)

## Open This Handbook When

- the question is about repository automation, verification, release support,
  docs integrity, or workflow fan-out
- you need to know which shared surface owns a repository-health rule
- the answer should stay above one product package boundary

## Open Another Handbook When

- the real question is about runtime, evidence, scoring, or lab behavior inside
  one product package
- you already know the issue belongs to one package API, CLI, or schema
- you are trying to understand product semantics rather than repository health

## What This Handbook Clarifies

- which repository-health questions belong to helper code, Make routing, or
  workflow automation
- where release, docs integrity, and policy enforcement live above package
  level
- when the correct route is to leave maintainer docs and hand the question back
  to a product package handbook

## Choose A Section

- open [bijux-proteomics-dev](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/) when the concern is
  helper code, schema drift, release support, or repository-health checks
- open [makes](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/makes/) when the concern is a shared command surface,
  package dispatch, or CI target family
- open [gh-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/) when the concern is GitHub Actions
  triggers, job trees, or docs and release publication

## Concrete Anchors

- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/` for maintainer
  helper code
- `Makefile` and `makes/` for shared command routing
- `.github/workflows/` for GitHub-triggered verification and publication
  automation
- `docs/08-bijux-proteomics-maintain/` for the maintainer handbook tree this
  page is routing through

## Bottom Line

This handbook makes repository-health work explicit and reviewable. It is not a
shadow product layer, and it sends readers back to the product package docs as
soon as the question becomes user-facing behavior.
