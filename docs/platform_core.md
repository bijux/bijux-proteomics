# Bijux Proteomics Core

## Mission

Build a protein R&D platform where deterministic execution, scientific evidence, human review, and lab planning are first-class from the start.

## Users

- computational biology engineers building reproducible workflows
- research scientists defining targets, constraints, and review gates
- platform engineers who need stable packages instead of one growing runtime

## Scientific Scope

- protein target programs
- evidence-backed candidate review
- experiment batch planning
- deterministic execution through the existing `agentic-proteins` runtime

## Non-Goals

- pretending the repository is only a single package
- hiding review and assay work behind generic workflow abstractions
- overcommitting to a Rust-first implementation before the product concepts are stable in Python

## Package Map

- `packages/agentic-proteins`: deterministic runtime, API, CLI, and artifact model
- `packages/bijux-proteomics-core`: program documents and runtime adapters
- `packages/bijux-proteomics-knowledge`: evidence bundles and gap analysis
- `packages/bijux-proteomics-lab`: assay batching and review queue planning

## Platform Pillars

- deterministic execution and provenance
- protein program definitions instead of raw sequences alone
- evidence coverage that explains why a candidate should advance
- human review gates before expensive steps
- experiment planning that makes lab work part of the architecture

## Next Expansion

- evidence ingestion from literature and assay systems
- richer run-to-program provenance back into `agentic-proteins`
- notebook and service surfaces for the umbrella platform
- future Rust core behind stable Python package boundaries
