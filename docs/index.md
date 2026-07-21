---
title: bijux-proteomics Documentation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Bijux Proteomics

`bijux-proteomics` is a composable Python platform for proteomics analysis,
reproducible execution, evidence-aware interpretation, and laboratory
follow-up. It is designed for work that must remain inspectable after a result
leaves the process that produced it.

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

## One result, six accountable layers

```mermaid
flowchart TD
    input["FASTA, mzML, spectra, search tables"]
    core["Scientific core\nmodels · algorithms · adapters · QC"]
    runtime["Execution runtime\nconfiguration · checkpoints · replay"]
    knowledge["Knowledge\nprovenance · grounding · contradictions"]
    intelligence["Intelligence\nranking · challenge · recommendation"]
    lab["Laboratory\nassays · readiness · outcomes"]
    foundation["Foundation\nidentity · schemas · canonical bytes"]
    input --> core --> runtime --> knowledge --> intelligence --> lab
    foundation --> core
    foundation --> runtime
    foundation --> knowledge
    foundation --> intelligence
    foundation --> lab
    lab -. evidence feedback .-> knowledge
```

The architecture separates computation from execution and separates evidence
from judgment. This matters when a run is repeated, a source is contradicted,
or a recommendation reaches the laboratory: each change has an identifiable
owner and can be reviewed without reconstructing hidden state.

## Scientific coverage

The implemented surface spans:

- sequence validation, digestion, amino-acid and peptide chemistry,
  modifications, isotope envelopes, and theoretical fragments;
- mzML and spectrum contracts, search-engine imports, PSM confidence,
  target-decoy review, contaminant audit, and protein inference;
- label-free quantification, DIA precursor and protein matrices, PTM review,
  targeted transitions, reproducibility, and QC;
- benchmark corpora, challenge assets, acceptance reports, and public case
  studies;
- evidence grounding, candidate ranking, recommendation challenge, and
  laboratory consequence.

Coverage is not a blanket accuracy claim. The public evidence currently
supports outsider-auditable DDA, DIA, PTM, and targeted workflow families;
bounded review-grade LFQ; and internal-only multiplex support. The
[workflow-family guide](01-bijux-proteomics/foundation/workflow-families.md)
explains the exact evidence ceiling.

## Choose a route

| You need to… | Start here |
| --- | --- |
| understand the system and its data flow | [Product architecture](01-bijux-proteomics/foundation/product-architecture.md) |
| inspect scientific algorithms and benchmark assets | [Core](04-bijux-proteomics-core/index.md) |
| run, resume, compare, or replay work | [Runtime](09-bijux-proteomics-runtime/index.md) |
| trace a claim to evidence and contradictions | [Knowledge](06-bijux-proteomics-knowledge/index.md) |
| rank candidates or challenge a recommendation | [Intelligence](05-bijux-proteomics-intelligence/index.md) |
| plan follow-up assays and capture outcomes | [Lab](07-bijux-proteomics-lab/index.md) |
| evolve schemas and stable identifiers | [Foundation](03-bijux-proteomics-foundation/index.md) |
| migrate historical execution callers | [agentic-proteins](02-agentic-proteins/index.md) |
| develop, validate, or release the repository | [Maintainer handbook](08-bijux-proteomics-maintain/index.md) |

## Trust model

Every defensible result has five independently inspectable forms:

1. **Scientific contract** — typed inputs, explicit assumptions, and a
   domain-specific result or refusal.
2. **Execution record** — configuration, provider choice, checkpoints,
   artifacts, and failure state.
3. **Evidence record** — citations, contexts, provenance, supporting and
   contradicting observations.
4. **Decision record** — ranking policy, sensitivity, counterfactuals,
   uncertainty, and recommendation posture.
5. **Consequence record** — requested assay, readiness decision, observed
   outcome, and feedback into the evidence base.

Canonical serialization and stable identifiers connect these forms without
collapsing their meanings. Missing evidence is represented as a limitation or
refusal, not converted into confidence by orchestration.

## Verification boundaries

Benchmark-backed support is workflow-specific. A successful execution proves
that a declared run completed under its recorded contract; it does not prove
biological truth. A grounded claim records support and contradiction; it does
not automatically authorize a recommendation. A recommendation does not
become validated until its downstream evidence and assay outcomes justify it.

Use [current capability limits](01-bijux-proteomics/foundation/current-capability-limits.md)
for unsupported or bounded areas and the
[release readiness matrix](01-bijux-proteomics/foundation/release-readiness-matrix.md)
for the current evidence gates.

## Public interfaces

- `bijux-proteomics` exposes the core scientific CLI.
- `bijux-proteomics-runtime` exposes canonical execution through a CLI and
  HTTP application.
- Python APIs are package-owned and re-exported through explicit public API
  modules.
- JSON documents use foundation serialization and compatibility contracts
  where they cross package or process boundaries.

Begin with the [repository handbook](01-bijux-proteomics/index.md) for package
selection, or go directly to the package that owns your scientific or
operational concern.
