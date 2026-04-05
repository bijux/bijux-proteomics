# Bijux Proteomics

**Scope:** Repository-level platform map for the Bijux Proteomics umbrella.
**Audience:** Contributors and reviewers who need the package map before changing code.
**Guarantees:** Names the platform pillars, package boundaries, and current execution surfaces.
**Non-Goals:** This page does not replace package-specific API or CLI documentation.

Why: the repository now contains multiple packages, so the home page needs to explain how deterministic execution, evidence, and lab planning fit together in one platform.

## Overview

Bijux Proteomics is the umbrella repository for protein R&D work. The deterministic runtime still lives in `agentic-proteins`, but the repository now also carries dedicated packages for program definitions, evidence bundles, and experiment planning. The runtime is implemented in [packages/agentic-proteins/src/agentic_proteins/interfaces/cli.py](https://github.com/bijux/bijux-proteomics/blob/main/packages/agentic-proteins/src/agentic_proteins/interfaces/cli.py), and repository consistency checks are enforced by [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py).

## Contracts

The umbrella contract is simple: `agentic-proteins` remains the execution product, `bijux-proteomics-core` defines stable program documents, `bijux-proteomics-knowledge` explains decisions with evidence, and `bijux-proteomics-lab` turns assay requirements into batches. Cross-package expectations are exercised in [tests/unit/platform/test_program_models.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/platform/test_program_models.py) and [tests/unit/platform/test_experiment_planner.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/platform/test_experiment_planner.py).

## Invariants

Deterministic execution still matters, but it is no longer the only story. Every serious program needs a target definition, explicit constraints, evidence coverage, and review gates before expensive work advances. The package move and path rules are checked by [tests/integration/test_agent_contracts.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/integration/test_agent_contracts.py), and the umbrella CLI template is covered by [tests/unit/platform/test_platform_cli.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/platform/test_platform_cli.py).

## Failure Modes

The repository becomes misleading when package boundaries blur, when a runtime change silently breaks platform packages, or when evidence and assay planning regress into ad hoc dictionaries. Those failures are reduced by keeping package code under `packages/`, validating documentation references with [scripts/check_docs_consistency.py](https://github.com/bijux/bijux-proteomics/blob/main/scripts/check_docs_consistency.py), and exercising evidence coverage with [tests/unit/platform/test_evidence_bundle.py](https://github.com/bijux/bijux-proteomics/blob/main/tests/unit/platform/test_evidence_bundle.py).

## Extension Points

The current Python-first shape leaves room for future model registries, assay ingestion adapters, notebook SDK surfaces, and eventually a Rust core without renaming the public concepts. New platform work should land in a package that matches its long-term role instead of being appended to the runtime by default. Package scaffolding lives under [packages/bijux-proteomics-core/pyproject.toml](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/pyproject.toml) and [packages/bijux-proteomics-lab/pyproject.toml](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-lab/pyproject.toml).

## Exit Criteria

This page is accurate when a new contributor can answer three questions quickly: what the umbrella platform is, which package owns a change, and how program definitions now connect evidence, review, and execution. A change is incomplete if those answers disappear from the repo landing surfaces or if the package map no longer matches the code under `packages/`.
