---
title: What Would Make This Repository Ready
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# What Would Make This Repository Ready

This page is generated from the current release matrix, acceptance dashboard, and package quality reports. It names the exact remaining blockers instead of broad roadmap language.

- source of truth: `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/hostile_review_pages.py`

## Blocking artifacts

These blockers keep the repository from claiming cleaner release posture because tracked artifacts, runtime evidence, or generated evidence are still not strong enough.

- `faithful-rerun-refused`: dda still refuses stronger rerun claims: faithful rerun still stops at imported MaxQuant and comparator exports because the repository does not own a raw DDA search execution lane; external-engine behavior remains proprietary or out-of-repository for the strongest DDA package
- `faithful-rerun-refused`: dia still refuses stronger rerun claims: the shipped DIA lane is raw-executable in runtime terms but still depends on library-conditioned exported reports rather than chromatogram-native replay
- `faithful-rerun-refused`: multiplex still refuses stronger rerun claims: multiplex remains below outsider-auditable trust because runtime rerun strength still outruns family-level consequence and challenge closure
- `black-box-language-outruns-rerun-evidence`: dda still requests outsider_auditable_bounded but the black-box benchmark dashboard only defends review_grade_bounded
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

## Workflow-family gaps

These blockers still weaken workflow-family trust because the current public sentence would outrun rerun, acceptance, or family-specific evidence.

- `multiplex` remains `internal_support_only` because acceptance still fails or stays intentionally narrowed: multiplex_interference, multiplex_channel_dropout, multiplex_reference_channel_fragility, multiplex_ratio_compression, multiplex_downstream_review_promotion

## Package-quality gaps

These blockers show where package maturity or cross-package release coverage still falls short of a repository-wide stronger claim.

- `agentic-proteins` is still not architectural-ready
- `bijux-proteomics-core` is still not architectural-ready
- `bijux-proteomics-dev` is still not architectural-ready
- `bijux-proteomics-foundation` is still not architectural-ready
- `bijux-proteomics-intelligence` is still not architectural-ready
- `bijux-proteomics-knowledge` is still not architectural-ready
- `bijux-proteomics-lab` is still not architectural-ready
- `bijux-proteomics-runtime` is still not architectural-ready

## Docs failures

These blockers show where public wording, routing, or scrutiny surfaces drift away from the evidence they are supposed to defend.

- `black-box-language-outruns-rerun-evidence`: dda still requests outsider_auditable_bounded but the black-box benchmark dashboard only defends review_grade_bounded
