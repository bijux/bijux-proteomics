# bijux-proteomics-knowledge

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/workflows/repo%20/%20verify/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-knowledge` models the evidence and claim layer behind protein
program decisions, including trust scoring, contradiction handling, and
decision-lineage structures.

Use this package when you need auditable evidence provenance, conflict-aware
knowledge management, and explicit reasoning about uncertainty and evidence
gaps.

## Why teams pick this package

- explicit evidence and claim models with trust and freshness semantics
- contradiction-aware resolution workflows that preserve audit history
- decision lineage structures for explainable governance and retrospectives
- compatibility with cross-package schema and serialization contracts

## Typical use cases

- store and score evidence used to advance or block protein program decisions
- detect conflicting claims and apply explicit resolution policies
- build auditable trails that explain why a conclusion changed over time
- surface unresolved knowledge gaps before committing lab or portfolio spend

## Installation

```bash
pip install bijux-proteomics-knowledge
```

## Quick start

```python
from bijux_proteomics_knowledge import evidence, claims, resolution, graph
from bijux_proteomics_knowledge.references import (
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    list_scientific_rules,
    resolve_ontology_mapping,
)
```

## Package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`
- Stable entrypoints: `evidence`, `claims`, `resolution`, `graph`, `review`, and `references`

## Package boundaries

This package owns evidence records, claim state, trust scoring, and contradiction resolution.

It does not own lifecycle gate transitions, ranking policy decisions, or experiment scheduling.

It also owns curated scientific reference knowledge that grounds shared evidence rules, benchmark claims, and ontology mappings.

## Contract checkpoints

- evidence and claim records must stay typed, auditable, and schema-versioned
- trust, freshness, and contradiction outputs must remain explicit instead of inferred
- resolution flows must preserve explainable lineage from evidence to decision
- downstream packages should depend on this layer for evidence semantics instead of re-scoring trust locally

## Curated scientific reference surfaces

- `references` exposes citation registries, ontology mappings, benchmark manifests, corpus manifests, scientific rule mappings, and read-only lookup helpers
- `references` also exposes scientific context entries, known-problem registries, literature groups, workflow claim and limitation narratives, and workflow briefing packets for downstream consumers
- bundled fixture corpora stay distinct from external scientific references so reproducibility claims remain auditable
- scientific rules carry explicit citation and benchmark context instead of relying on package-local assumptions
- workflow briefing packets keep claim surfaces, limitation surfaces, and provenance attached so intelligence and lab can consume grounded context without re-curating it locally

## Choose this package when

- you need evidence, claim, contradiction, or lineage semantics
- auditability and review traceability are part of the contract
- multiple higher layers should share the same trust and resolution model

## Route elsewhere when

- the change defines lifecycle authority, ranking policy, lab scheduling, or
  transport-bound payload shaping
- the helper only reformats evidence results for operator interfaces
- the behavior exists for one scoring or lab workflow instead of shared evidence meaning

## Verification route

- check `tests` for evidence, resolution, graph, and schema proof before
  treating a knowledge change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when ownership or trust-semantics claims are part of the change
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

## Review questions

- does the change preserve evidence, contradiction, lineage, or trust semantics
  rather than transport-bound presentation or workflow-local shaping
- would another package start carrying shadow evidence interpretation if this
  behavior stayed outside knowledge
- can the change be justified without claiming lifecycle, ranking, lab
  execution, or runtime interface ownership

## Escalation route

- route the change outward when the behavior mainly defines lifecycle
  progression, ranking policy, lab execution, or interface transport
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the
  proposal starts looking like presentation reshaping instead of shared evidence
  meaning
- escalate before release when downstream consumers would need package-specific
  trust or lineage exceptions to adopt the change

## Consumer impact signals

- expect downstream review when evidence rules, lineage semantics, or trust
  resolution behavior change because other layers consume those meanings
- treat changes that alter contradiction handling, claim interpretation, or
  lineage expectations as high-impact even when APIs stay stable
- expect a narrower release burden when the change only improves internal
  implementation without changing evidence semantics

## Explicit non-goals

- this package does not own runtime orchestration, provider wiring, or replay
  behavior
- this package does not define ranking policy or lab-specific scheduling logic
- this package does not carry shared primitive contracts that belong in the
  foundation package

## Source guide

- [`src/bijux_proteomics_knowledge/evidence.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/evidence.py) for evidence models, scoring, and contradiction detection
- [`src/bijux_proteomics_knowledge/resolution.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/resolution.py) for conflict-resolution policies
- [`src/bijux_proteomics_knowledge/graph.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/graph.py) for evidence-graph validation rules
- [`src/bijux_proteomics_knowledge/claims.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/claims.py) for claim modeling and knowledge-gap audits
- [`src/bijux_proteomics_knowledge/references/`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/references) for curated citations, ontology mappings, benchmark manifests, corpus manifests, scientific rules, and read-only query helpers
- [`src/bijux_proteomics_knowledge/references/briefings.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/references/briefings.py) for workflow-level claim, limitation, context, literature, problem, and rule packets that preserve provenance for downstream consumers
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-knowledge/tests) for executable behavior expectations

## Documentation

- [Package guide](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/)
- [Release and versioning](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/release-and-versioning/)
