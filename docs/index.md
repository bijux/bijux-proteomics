---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Bijux Proteomics

`bijux-proteomics` is a deliberately split system for deterministic protein
runtime execution, shared contracts, decision intelligence, evidence handling,
and lab orchestration. The split is the architecture, not a packaging detail.

Start here when you need repository-level orientation. A new reader should be
able to see why the repository is split, which package owns the current
concern, and which checked-in files back the explanation.

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Release PyPI](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-7%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-7-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

<div class="bijux-callout"><strong>Start with the package split, not the file tree.</strong>
Foundation keeps shared payload meaning stable. Core defines program and
lifecycle contracts. Knowledge tracks claims and evidence state. Intelligence
turns those inputs into inspectable decisions. Lab carries assay planning and
outcomes. <code>bijux-proteomics-runtime</code> governs execution and replay.
<code>agentic-proteins</code> preserves compatibility entrypoints. The
repository handbook exists to explain how those responsibilities fit together
without pretending they are one thing.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Whole-System Idea</h3><p>Use the root pages to understand why the repository is split and how the proteomics packages fit into one accountable flow.</p></div>
  <div class="bijux-panel"><h3>Honesty Rule</h3><p>Use the docs as a map, then verify the claim in code, schema artifacts, tests, or workflows before treating it as settled.</p></div>
  <div class="bijux-panel"><h3>Fast Reading Path</h3><p>Open the repository handbook for cross-package questions, one product handbook for owned behavior, and the maintainer handbook for repository health.</p></div>
</div>

<div class="bijux-quicklinks">
<a class="md-button md-button--primary" href="01-bijux-proteomics/">Open the repository handbook</a>
<a class="md-button" href="08-bijux-proteomics-maintain/">Open maintenance docs</a>
</div>

## Visual Summary

```mermaid
flowchart TB
    page["Bijux Proteomics<br/>clarifies: repository section | maintainer section | package handbooks"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    detail1["why the split exists"]
    detail1 --> page
    detail2["where each package takes authority"]
    detail2 --> page
    detail3["which handbook branch to open first"]
    detail3 --> page
    detail4["maintainer work"]
    detail4 --> page
    detail5["questions that do not belong on the landing page"]
    detail5 --> page
    next1["repository handbook"]
    page --> next1
    next2["product package docs"]
    page --> next2
    next3["maintainer docs"]
    page --> next3
    class page page;
    class detail1,detail2,detail3,detail4,detail5 anchor;
    class next1,next2,next3 action;
```

## Start Here

- open [bijux-proteomics](01-bijux-proteomics/index.md) when the question crosses
  package boundaries or touches shared governance
- open one product package when you need ownership, interfaces, operations, or
  proof for one package
- open [bijux-proteomics-maintain](08-bijux-proteomics-maintain/index.md) for
  repository automation, schema enforcement, and maintainer-only guardrails

## Package Flow

| Package | Owns | Open It When |
| --- | --- | --- |
| `bijux-proteomics-runtime` | runtime execution, replay, and operator-facing orchestration | you need the execution authority layer |
| `agentic-proteins` | compatibility forwarding package for legacy runtime imports and entrypoints | you need migration-safe legacy import or CLI paths |
| `bijux-proteomics-foundation` | schema compatibility and canonical serialization primitives | you are changing shared payload meaning |
| `bijux-proteomics-core` | program definitions, constraints, and lifecycle contracts | you are changing program or gate behavior |
| `bijux-proteomics-intelligence` | scoring, ranking, and explainable decision logic | you are tuning recommendations or policy |
| `bijux-proteomics-knowledge` | evidence records, claim state, and contradiction handling | the work concerns trust or evidence state |
| `bijux-proteomics-lab` | experiment planning, assay outcomes, and closed-loop lab artifacts | the work concerns lab execution or outcome promotion |

## Documentation Scope

- the `bijux-proteomics` repository handbook
- the `bijux-proteomics-maintain` maintainer handbook
- the product package handbooks published from this repository

## Purpose

Use this page to get oriented quickly, choose the right handbook branch, and
move to the files that carry the detailed proof.

## Stability

Keep it aligned with the sections rendered in `docs/`, the packages that still
ship from this repository, and the reasons the split exists.
