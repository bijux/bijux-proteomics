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

This site is meant to stand on its own. A new reader should be able to answer
three questions quickly: why the repository is split, which package owns the
current concern, and which checked-in files prove the story being told.

[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR bundles](https://img.shields.io/badge/ghcr-06%20bundles-181717?logo=github)](https://github.com/orgs/bijux/packages?repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-06-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![Agentic docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/agentic-proteins/)
[![Foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-foundation/)
[![Core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-core/)
[![Intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-intelligence/)
[![Knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-knowledge/)
[![Lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/bijux-proteomics-lab/)

<div class="bijux-callout"><strong>Start with the package split, not the file tree.</strong>
Foundation keeps shared payload meaning stable. Core defines program and
lifecycle contracts. Knowledge tracks claims and evidence state. Intelligence
turns those inputs into inspectable decisions. Lab carries assay planning and
outcomes. <code>agentic-proteins</code> governs execution and replay. The
repository handbook exists to explain how those responsibilities fit together
without pretending they are one thing.</div>

<div class="bijux-panel-grid">
  <div class="bijux-panel"><h3>Whole-System Idea</h3><p>Use the root pages to understand why the repository is split and how the proteomics packages fit into one accountable flow.</p></div>
  <div class="bijux-panel"><h3>Honesty Rule</h3><p>The docs are only useful if they send readers back to code, schema artifacts, tests, and workflows quickly enough to verify the claims.</p></div>
  <div class="bijux-panel"><h3>Fast Reading Path</h3><p>Open the repository handbook for cross-package questions, one product handbook for owned behavior, and the maintainer handbook for repository health.</p></div>
</div>

<div class="bijux-quicklinks">
<a class="md-button md-button--primary" href="bijux-proteomics/">Open the repository handbook</a>
<a class="md-button" href="bijux-proteomics-maintain/">Open maintenance docs</a>
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

- open [bijux-proteomics](bijux-proteomics/index.md) when the question crosses
  package boundaries or touches shared governance
- open one product package when you need ownership, interfaces, operations, or
  proof for one package
- open [bijux-proteomics-maintain](bijux-proteomics-maintain/index.md) for
  repository automation, schema enforcement, and maintainer-only guardrails

## Package Flow

| Package | Owns | Open It When |
| --- | --- | --- |
| `agentic-proteins` | runtime execution, replay, and operator-facing orchestration | you need the execution authority layer |
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

This page is the front door to the handbook. Its job is to make the split
legible quickly enough that a reader can choose the right next section before
they drown in detail.

## Stability

Keep it aligned with the sections rendered in `docs/`, the packages that still
ship from this repository, and the reasons the split exists.
