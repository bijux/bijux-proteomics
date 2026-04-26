---
title: gh-workflows
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# gh-workflows

Open this section to understand the GitHub Actions entrypoints and reusable
building blocks that verify, release, and document the repository.

Open these pages when you need to know which workflow starts on push, pull
request, tag, or manual dispatch, and how that entrypoint fans out into
repository checks, package matrices, or documentation publication.

The top-level entrypoints are `verify.yml` for pushes and pull requests,
`deploy-docs.yml` for handbook publication from `main`, and the release split
workflows (`release-artifacts.yml`, `release-github.yml`, `release-pypi.yml`,
`release-ghcr.yml`) for tag-driven publication. `ci.yml` is the reusable CI
wrapper called by `verify.yml`.

```mermaid
flowchart LR
    verify["verify.yml<br/>push and pull request checks"]
    docs["deploy-docs.yml<br/>publish handbook"]
    release["release workflows<br/>artifacts, github, pypi, ghcr"]
    reusable["reusable workflow<br/>ci.yml"]
    reader["reader question<br/>which workflow owns this automation path?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class verify,page reader;
    class docs,release,reusable positive;
    verify --> reader
    docs --> reader
    release --> reader
    reusable --> reader
```

## Pages In gh-workflows

- [verify](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/verify/)
- [reusable-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/reusable-workflows/)
- [deploy-docs](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/deploy-docs/)
- [release-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/release-workflows/)

## Open This Section When

- the concern is about workflow triggers, job trees, or reusable workflow
  composition
- you need to know which GitHub Actions file owns verification, docs
  publication, or release automation
- the answer should come from checked-in workflow contracts rather than CI
  folklore

## Open Another Section When

- the question is about Make target routing rather than GitHub Actions
- the issue belongs to one product package contract instead of repository
  automation
- you only need maintainer helper code rather than workflow entrypoints

## Choose A Page

- open [verify](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/verify/) when the concern starts from push or pull request
  verification
- open [deploy-docs](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/deploy-docs/) when the concern is handbook publication
  from `main`
- open [release-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/release-workflows/) when the concern is
  tag-driven publication
- open [reusable-workflows](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/gh-workflows/reusable-workflows/) when the key question is job
  reuse or nested workflow composition

## Reader Takeaway

This section makes workflow ownership visible enough that a maintainer can move
from an automation symptom to the right workflow file without relying on CI
archaeology.

## What You Get

This page gives you the route from an automation symptom to the workflow page
that explains the owning trigger and job tree.
