---
title: Why This Repository Is Not Ready Yet
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Why This Repository Is Not Ready Yet

This page is generated from the current release-readiness matrix. It exists so blocked release bars stay visible in plain language and cannot be softened manually.

- blocked release bars: 4
- source of truth: `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/release_readiness_matrix.py`

## Black-box rerunability

A hostile reviewer should be able to start from the flagship runtime lane and see whether rerun evidence is strong enough without maintainers narrating around missing artifacts.

Evidence paths:
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/black_box_reproducibility.py`
- `docs/09-bijux-proteomics-runtime/runtime-execution-boundary.md`
- `docs/09-bijux-proteomics-runtime/black-box-run-verification.md`
- `docs/09-bijux-proteomics-runtime/raw-versus-import-execution.md`
- `docs/09-bijux-proteomics-runtime/runtime-replay-challenges.md`
- `docs/09-bijux-proteomics-runtime/runtime-environment-contracts.md`
- `docs/09-bijux-proteomics-runtime/runtime-artifact-stability.md`
- `docs/09-bijux-proteomics-runtime/runtime-rerun-refusals.md`
- `docs/09-bijux-proteomics-runtime/black-box-benchmark-dashboard.md`
- `docs/09-bijux-proteomics-runtime/benchmark-rerun-kits.md`
- `docs/09-bijux-proteomics-runtime/benchmark-comparability-matrix.md`
- `docs/01-bijux-proteomics/foundation/public-artifact-index.md`
- `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`

Current blockers:
- `faithful-rerun-refused`: dda still refuses stronger rerun claims: faithful rerun still stops at imported MaxQuant and comparator exports because the repository does not own a raw DDA search execution lane; external-engine behavior remains proprietary or out-of-repository for the strongest DDA package
- `faithful-rerun-refused`: dia still refuses stronger rerun claims: the shipped DIA lane is raw-executable in runtime terms but still depends on library-conditioned exported reports rather than chromatogram-native replay
- `faithful-rerun-refused`: multiplex still refuses stronger rerun claims: multiplex remains below outsider-auditable trust because runtime rerun strength still outruns family-level consequence and challenge closure
- `black-box-language-outruns-rerun-evidence`: dda still requests outsider_auditable_bounded but the black-box benchmark dashboard only defends review_grade_bounded

## Benchmark asset quality

Release claims must stay behind the benchmark asset coverage, grounding, and scientific release evidence actually checked in.

Evidence paths:
- `configs/package-governance/scientific-release-workflows.toml`
- `docs/04-bijux-proteomics-core/foundation/benchmark-freshness-review.md`
- `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`
- `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

Current blockers:
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: compatibility-bridge: orchestration/__init__.py still imports compatibility modules instead of canonical owners: agentic_proteins.orchestration.bridge_contracts
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: compatibility-bridge: orchestration/bridge_contracts.py is classified as canonical instead of wrapper or dead
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: compatibility-bridge: orchestration/bridge_contracts.py still defines local compatibility logic: BridgeSurfaceContract, CompatibilityRetirementBudget, list_bridge_surface_contracts, build_bridge_retirement_budget
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'EvidenceFreshnessState' is owned by multiple canonical packages: bijux-proteomics-intelligence:bijux_proteomics_intelligence/reviews/boards.py, bijux-proteomics-knowledge:bijux_proteomics_knowledge/memory/models/evidence.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'WorkflowReplayProofReport' is owned by multiple canonical packages: bijux-proteomics-knowledge:bijux_proteomics_knowledge/references/workflows/replay_proof.py, bijux-proteomics-runtime:bijux_proteomics_runtime/workflows/plans.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: agentic-proteins exposes 111 wrapper modules across 117 source modules
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: orchestration/__init__.py still imports compatibility modules instead of canonical owners: agentic_proteins.orchestration.bridge_contracts
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: orchestration/bridge_contracts.py is classified as canonical instead of wrapper or dead
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: orchestration/bridge_contracts.py still defines local compatibility logic: BridgeSurfaceContract, CompatibilityRetirementBudget, list_bridge_surface_contracts, build_bridge_retirement_budget
- `outsider-packet-claim-missing`: dda outsider packet is missing the grounded claim text: The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, and lab consequence without maintainer narration.
- `outsider-packet-claim-missing`: dia outsider packet is missing the grounded claim text: The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, and lab consequence without maintainer narration.
- `outsider-packet-claim-missing`: ptm outsider packet is missing the grounded claim text: The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, and lab consequence without maintainer narration.
- `outsider-packet-claim-missing`: lfq outsider packet is missing the grounded claim text: The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, and lab consequence without maintainer narration.
- `trust-surface-claim-missing`: multiplex trust surface is missing the grounded claim text: It has a real public package, a raw-executable runtime lane, and explicit chemistry pressure, plus one companion stress package and one published cross-package report, but it still lacks a dedicated outsider review packet and a dedicated lab consequence packet.
- `outsider-packet-claim-missing`: targeted outsider packet is missing the grounded claim text: The outsider packet exists to let a skeptical reviewer inspect the current flagship workflow posture from tracked files, runtime evidence, scientific reading, recommendation logic, and lab consequence without maintainer narration.

## Docs clarity

Root and handbook wording must route readers to the right evidence without stronger trust language than the current docs surfaces can honestly defend.

Evidence paths:
- `README.md`
- `docs/index.md`
- `docs/01-bijux-proteomics/foundation/product-architecture.md`
- `docs/01-bijux-proteomics/foundation/cross-package-ownership.md`
- `docs/01-bijux-proteomics/foundation/release-readiness-matrix.md`

Current blockers:
- `black-box-language-outruns-rerun-evidence`: dda still requests outsider_auditable_bounded but the black-box benchmark dashboard only defends review_grade_bounded

## Package-boundary stability

Import directions, public surfaces, and README routing must continue to describe the same ownership model.

Evidence paths:
- `configs/package-governance/package-dependency-policy.toml`
- `configs/package-governance/repository-product-shape.toml`
- `docs/01-bijux-proteomics/foundation/cross-package-ownership.md`

Current blockers:
- `release-contract-failure`: bijux-proteomics-core imports disallowed package edges: bijux-proteomics-knowledge
- `release-contract-failure`: bijux-proteomics-intelligence imports disallowed package edges: bijux-proteomics-lab, bijux-proteomics-runtime
- `release-contract-failure`: bijux-proteomics-runtime imports disallowed package edges: bijux-proteomics-knowledge, bijux-proteomics-lab
