# Bijux Proteomics

**Python-first protein R&D platform for reproducible execution, evidence-backed decisions, and experiment planning.**

This repository is no longer a single-package codebase. It is the umbrella for multiple packages that together shape a more serious proteomics platform:

- `agentic-proteins` remains the deterministic execution and orchestration product.
- `bijux-proteomics-core` defines durable program models, review gates, and execution adapters.
- `bijux-proteomics-intelligence` turns program intent into design briefs, candidate ranking logic, and explicit liabilities.
- `bijux-proteomics-knowledge` stores evidence bundles that explain why a target or candidate should advance.
- `bijux-proteomics-lab` turns assay requirements into ordered experiment batches.

## Why This Repo Exists

The earlier shape was strong on reproducibility but too narrow: it looked more like computer science around proteins than a protein R&D platform. Bijux Proteomics adds the missing scientific frame around that runtime:

- protein targets and program definitions
- explicit evidence requirements
- human review gates before expensive work
- assay planning for wet-lab follow-up
- a package map that can grow without collapsing into one giant distribution

## Package Map

| Package | Role | Current surface |
| ------- | ---- | --------------- |
| `packages/agentic-proteins` | Deterministic runtime, CLI, API, artifact model | `agentic-proteins` CLI |
| `packages/bijux-proteomics-foundation` | Shared schema metadata and JSON document helpers | Python models |
| `packages/bijux-proteomics-core` | Program specifications and execution adapters | `bijux-proteomics` CLI |
| `packages/bijux-proteomics-intelligence` | Design briefs, liabilities, and candidate ranking | Python models |
| `packages/bijux-proteomics-knowledge` | Evidence bundles and gap analysis | Python models |
| `packages/bijux-proteomics-lab` | Experiment batching and review queue generation | Python helpers |

## Kickstart Workflow

```bash
# Existing runtime product
pip install -e .
agentic-proteins run --sequence "ACDEFGHIKLMNPQRSTVWY"

# Platform program scaffolding
PYTHONPATH=packages/bijux-proteomics-core/src:packages/bijux-proteomics-intelligence/src:packages/bijux-proteomics-knowledge/src:packages/bijux-proteomics-lab/src \
  .venv/bin/python -m bijux_proteomics.cli program-template \
  --program-id kinase-rescue \
  --name "Kinase Rescue" \
  --objective "recover activity while constraining aggregation" \
  --target-id kinase-x \
  --target-name "Kinase X" \
  --sequence ACDEFGHIKLMNPQRSTVWY \
  --organism human \
  --mechanism "stabilize the active conformation" \
  --out artifacts/test/kinase-rescue.json
```

## Repository Layout

```text
api/                                  OpenAPI schemas for Agentic Proteins
config/                               Lint, typing, and coverage config
docs/                                 MkDocs site for the umbrella repo
packages/agentic-proteins/            Existing deterministic runtime product
packages/bijux-proteomics-foundation/ Shared document and schema primitives
packages/bijux-proteomics-core/       Program models and execution adapters
packages/bijux-proteomics-intelligence/ Protein reasoning, ranking, and liabilities
packages/bijux-proteomics-knowledge/  Evidence bundle package
packages/bijux-proteomics-lab/        Experiment planning package
scripts/                              Repository automation and consistency checks
packages/agentic-proteins/tests/ Cross-package unit, integration, and regression tests
```

## Design Direction

The architecture is centered on:

- deterministic core execution
- protein intelligence and candidate ranking
- protein intelligence and decision context
- human review and approval points
- lab planning and feedback loops
- evidence memory that explains program decisions
- candidate ranking that stays legible to reviewers

The short architecture note is in `docs/platform_core.md`.

## Resources

- Repository: https://github.com/bijux/bijux-proteomics
- Issues: https://github.com/bijux/bijux-proteomics/issues
- Security reports: https://github.com/bijux/bijux-proteomics/security/advisories/new
- Package runtime docs: https://bijux.github.io/bijux-proteomics/
- Agentic Proteins package README: `packages/agentic-proteins/README.md`

## License

Apache-2.0. See `LICENSE`.
