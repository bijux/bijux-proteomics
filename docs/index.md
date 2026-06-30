---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Bijux Proteomics

`bijux-proteomics` is a bounded proteomics product for benchmark-backed
scientific workflows, reviewable execution, grounded interpretation,
recommendation posture, and explicit downstream lab consequence.

The important correction since `v0.3.7` is that this repository is no longer
best described as governance around isolated packages. It now has a deeper
scientific core, public benchmark packets, runtime rerun proof, explicit
knowledge and intelligence pressure, and a lab-consequence owner that keeps the
cost of being wrong visible.

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

## Product Scope

This site should let a serious reader answer four questions quickly:

- what scientific workflow families the repository can defend today
- which package owns each part of that defense
- where benchmark, runtime, grounding, recommendation, and lab consequence
  still cap the wording
- which page should be opened next without maintainer narration

## Current Credible Workflow Families

The strongest current public sentence is family-specific rather than
repository-wide:

- outsider-auditable today: `dda`, `dia`, `ptm`, `targeted`
- review-grade but still bounded: `lfq`
- internal support only: `multiplex`

That sentence is carried by paired benchmark packages, runtime rerun evidence,
grounded claim review, recommendation challenge, and lab-consequence
boundaries. It is not carried by polished prose alone.

## Forbidden Claims

This home page should never imply the following:

- that one strong workflow family upgrades the whole repository to
  decision-grade authority
- that public benchmark depth erases runtime, grounding, recommendation, or
  assay-burden limits
- that raw-executable runtime lanes automatically create broader scientific
  truth
- that recommendation confidence can outrun the weakest downstream lab
  consequence

When wording sounds stronger than the weakest owner surface, the right next
page is [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/).

## Reader Paths

- Scientist: start with
  [Scientist Journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/)
  when the question is what one careful scientific reader should trust and why.
- Operator: start with the
  [Operator Rerun Journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
  when the question is how to reopen a flagship family without guessing what
  runtime proof surface counts.
- Maintainer: start with
  [Maintainer Safe Change](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change/)
  when the question is how to evolve the repository without widening dishonest
  language.

## Reader-First Sections

Open these sections in order if you need the shortest honest route through the
product:

1. [Product Overview](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-overview/)
2. [Product Architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
3. [Cross-Package Ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
4. [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
5. [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)

If the question is already owner-specific, jump directly to:

- evidence root:
  [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
- runtime proof:
  [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
- grounded belief:
  [Workflow Claim Grounding](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/workflow-claim-grounding/)
- recommendation posture:
  [Workflow Recommendation Confidence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/foundation/workflow-recommendation-confidence/)
- downstream follow-up:
  [Lab Consequence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/lab-consequence/)

## Package Owners

The site is organized around durable package ownership:

| handbook | owner question |
| --- | --- |
| `01-bijux-proteomics` | what the repository claims, where it stops, and how package boundaries fit together |
| `02-agentic-proteins` | which historical runtime entrypoints still exist and how compatibility is bounded |
| `03-bijux-proteomics-foundation` | which shared contracts and serialization rules keep scientific state stable |
| `04-bijux-proteomics-core` | where public benchmark assets and flagship scientific workflow contracts live |
| `05-bijux-proteomics-intelligence` | how recommendations are challenged, narrowed, or refused |
| `06-bijux-proteomics-knowledge` | what the repository can ground scientifically and where contradiction remains |
| `07-bijux-proteomics-lab` | what downstream assay burden, refusal, and learning loops still apply |
| `08-bijux-proteomics-maintain` | how maintainers verify, release, and keep the repository honest |
| `09-bijux-proteomics-runtime` | how public benchmark packages become rerunnable runtime evidence |

## What Changed Since v0.3.7

The docs now need to represent a deeper product:

- broader core biology and chemistry surfaces across sequence handling,
  digestion, spectra, mzML, quantification, DIA, PTM, and review artifacts
- stronger runtime proof through replay, rerun kits, refusal routes, and
  artifact-integrity surfaces
- explicit knowledge and intelligence routes for grounding, contradiction,
  downgrade, overconfidence, and regret
- a real lab-consequence owner that keeps follow-up burden, refusal, and
  requested-versus-observed learning public

## Boundary

This home page should make the product legible and point to the real owner
next. It should not duplicate package-handbook detail once the right owner is
known.
