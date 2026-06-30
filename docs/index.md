---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# Bijux Proteomics

`bijux-proteomics` is a bounded proteomics product for benchmark-backed
execution, scientific review, recommendation posture, and lab consequence.

The package split exists so those steps stay reviewable, but the reader should
not have to learn the package tree before they can learn the product. Short
install aliases now reserve `bijux-proteomics`, `proteomics`, and the
family-scoped `proteomics-*` names without creating second owner packages, and
`agentic-proteins` remains the legacy compatibility install for historical
runtime entrypoints.

## Product Scope

- repository-level route:
  [Product Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
- end-to-end lifecycle:
  [Product Architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- owner map and handoff boundaries:
  [Cross-Package Ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)

## 0.3.8 Release Snapshot

- `foundation` now owns the durable kernel for identifiers, compatibility,
  serialization, and stable shared outcomes used across release gates.
- `core` now owns the first broad public scientific workflow surface from
  FASTA intake through QC and workflow planning, with benchmark-backed docs and
  walkthrough routes.
- `runtime` is now the canonical execution package for replay, rerun kits,
  operator handoff, and public runtime-proof routes.
- `knowledge`, `intelligence`, and `lab` now keep grounding,
  recommendation posture, and assay consequence explicit instead of hiding
  them behind core or runtime prose.
- reader-first product routes now live inside numbered handbook owners rather
  than extra top-level journey directories.

## Current Credible Workflow Families

Outsider-auditable today: `dda`, `dia`, `ptm`, `targeted`.

Review-grade-bounded today: `lfq`.

Internal-support-only today: `multiplex`.

The shortest hostile-review route is:

- [Flagship release candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
- [Workflow families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
- [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
- [Decision support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)

## Forbidden Claims

- no broad proteomics workflow coverage claim beyond the checked workflow families
- no release-ready, reference-grade, elite, or product-grade wording
- no stronger lab confidence than the downstream evidence chain supports

See
[Current capability limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)
for the live limit list.

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-15%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-15-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

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

## Start By Question

- Start with
  [Product Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
  when you need the shortest explanation of what the product claims today.
- Start with
  [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
  when you need to know which workflow families are publishable, bounded, or
  still internal only.
- Start with
  [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when you need to inspect the evidence roots behind a workflow claim.
- Start with
  [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  when the question is how a benchmark-backed workflow actually gets rerun.
- Start with
  [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is why a recommendation changed or what consequence logic
  is being applied.
- Start with
  [Lab Consequence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lab-consequence/)
  when the question is what downstream assay burden, refusal, or learning loop
  a workflow result creates.
- Start with
  [Maintenance](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintenance-overview/)
  when the question is which gate, report, or release checkpoint governs a
  repository change.

## Role-Based Starts

- Scientist:
  [Scientist Journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/)
- Operator:
  [Operator Rerun Journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
- Maintainer:
  [Maintainer Safe Change](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change/)

## Package Family At A Glance

<code>bijux-proteomics-runtime</code> governs execution and replay.
<code>agentic-proteins</code> preserves compatibility entrypoints.

| Package | Owns |
| --- | --- |
| `bijux-proteomics-foundation` | shared contracts, identifiers, and deterministic serialization |
| `bijux-proteomics-core` | benchmark assets, durable scientific contracts, and workflow requests |
| `bijux-proteomics-runtime` | execution, provider binding, deterministic replay, and operator entrypoints |
| `bijux-proteomics-knowledge` | scientific memory, provenance, contradiction handling, and review state |
| `bijux-proteomics-intelligence` | recommendation posture, ranking sensitivity, and refusal behavior |
| `bijux-proteomics-lab` | assay consequence planning, readiness, and observed outcomes |

## Install Aliases

Canonical owner packages stay the product reference surface. Alias and
compatibility distributions exist so the same package owners can also be
installed under the shorter, reserve-worthy, or migration-safe names below.

| Install surface | Canonical owner package |
| --- | --- |
| `agentic-proteins` | `bijux-proteomics-runtime` plus legacy compatibility submodules |
| `bijux-proteomics` | `bijux-proteomics-core` |
| `proteomics` | `bijux-proteomics-core` |
| `proteomics-core` | `bijux-proteomics-core` |
| `proteomics-foundation` | `bijux-proteomics-foundation` |
| `proteomics-runtime` | `bijux-proteomics-runtime` |
| `proteomics-intelligence` | `bijux-proteomics-intelligence` |
| `proteomics-knowledge` | `bijux-proteomics-knowledge` |
| `proteomics-lab` | `bijux-proteomics-lab` |

## Numbered Handbook Owners

- `01-bijux-proteomics` owns root product framing, trust limits, release
  posture, and cross-package boundaries.
- `02-agentic-proteins` owns legacy compatibility entrypoints and the
  migration bridge into canonical runtime ownership.
- `03-bijux-proteomics-foundation` owns shared contracts and serialization
  primitives.
- `04-bijux-proteomics-core` owns benchmark-backed scientific workflow
  contracts and public benchmark assets.
- `05-bijux-proteomics-intelligence` owns interpretation posture,
  recommendation challenge routes, and learning-facing judgment.
- `06-bijux-proteomics-knowledge` owns grounded scientific memory,
  contradiction review, and claim grounding.
- `07-bijux-proteomics-lab` owns assay consequence, refusal routes, and
  outcome learning.
- `08-bijux-proteomics-maintain` owns repository quality, release, and
  maintainer operations.
- `09-bijux-proteomics-runtime` owns execution, replay, rerun comparability,
  and operator-facing runtime proof.

## Boundary

This page should give the reader one useful next question in one hop. It
should not make numbered package routes do the first job that a product home
page should do itself.
