# platform_core

**Scope:** Repository mission, package ownership, and platform pillars for Bijux Proteomics.
**Audience:** Contributors who need the repository intent before editing a package.
**Guarantees:** States the stable package map and the reason the umbrella platform exists.
**Non-Goals:** This page does not replace package-level API, CLI, or runtime documents.

Why: the repository now contains multiple packages, so the platform intent belongs in the maintained docs tree.

## Overview

Bijux Proteomics joins deterministic execution, evidence review, and experiment planning in one repository. Read [index.md](index.md) for the landing map. Read [overview/getting_started.md](overview/getting_started.md) for local setup. Runtime execution lives in [packages/agentic-proteins/src/agentic_proteins/interfaces/cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/interfaces/cli.py). Program models live in [packages/bijux-proteomics-core/src/bijux_proteomics/programs.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/programs.py).

## Contracts

Each package owns one durable role. [governance/core.md](governance/core.md) defines the broad governance frame. [architecture/architecture.md](architecture/architecture.md) describes the runtime shape. `agentic-proteins` owns execution. `bijux-proteomics-core` owns program definitions. `bijux-proteomics-intelligence` owns design briefs and candidate ranking. `bijux-proteomics-knowledge` owns evidence bundles. `bijux-proteomics-lab` owns experiment planning. Those boundaries are exercised by [packages/bijux-proteomics-core/tests/test_program_models.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/tests/test_program_models.py), [packages/bijux-proteomics-intelligence/tests/test_candidate_ranking.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/tests/test_candidate_ranking.py), and [packages/bijux-proteomics-lab/tests/test_experiment_planner.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/tests/test_experiment_planner.py).

## Invariants

The platform does not stop at sequence execution. [concepts/core_concepts.md](concepts/core_concepts.md) describes the shared language. [architecture/invariants.md](architecture/invariants.md) records the stable system rules. Every program needs targets, constraints, evidence needs, review gates, assay plans, and a transparent candidate brief. Those rules are encoded in [packages/bijux-proteomics-core/src/bijux_proteomics/programs.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/programs.py), [packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py), and [packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/evidence.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/evidence.py).

## Failure Modes

The platform drifts when package ownership blurs. [meta/NAMING.md](meta/NAMING.md) guards naming quality. [meta/SPINE.md](meta/SPINE.md) guards doc placement. Root tooling drift is also a risk. Evidence and assay work fail when treated as side notes. These cases are reduced by [packages/bijux-proteomics-knowledge/tests/test_evidence_bundle.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-knowledge/tests/test_evidence_bundle.py) and [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).

## Extension Points

New work attaches to a durable package role. [architecture/execution_model.md](architecture/execution_model.md) records execution constraints. [research/system_schematic.md](research/system_schematic.md) records the broader system picture. Model registries can extend [packages/bijux-proteomics-core/src/bijux_proteomics/runner.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/runner.py). Candidate reasoning can extend [packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence/briefs.py). Assay orchestration can extend [packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py).

## Exit Criteria

This page succeeds when a contributor can explain the repository mission. [index.md](index.md) and [governance/positioning.md](governance/positioning.md) must stay aligned with it. The reader must also identify the right package for a change. The reader must also describe how execution, evidence, and experiment planning connect. The platform story has regressed if those answers move back into scattered root notes.
