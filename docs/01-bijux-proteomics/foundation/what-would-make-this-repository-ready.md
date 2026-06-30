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
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditEntry' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditReport' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditSummary' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: bijux-proteomics-core exposes 133 thin modules and needs tighter ownership boundaries

## Workflow-family gaps

These blockers still weaken workflow-family trust because the current public sentence would outrun rerun, acceptance, or family-specific evidence.

- `lfq` remains `review_grade_bounded` because acceptance still fails or stays intentionally narrowed: lfq_missingness_burden, lfq_normalization_drift
- `multiplex` remains `internal_support_only` because acceptance still fails or stays intentionally narrowed: multiplex_interference, multiplex_channel_dropout, multiplex_reference_channel_fragility, multiplex_ratio_compression, multiplex_downstream_review_promotion

## Package-quality gaps

These blockers show where package maturity or cross-package release coverage still falls short of a repository-wide stronger claim.

- `agentic-proteins` is still not architectural-ready
- `bijux-proteomics` is still not architectural-ready
- `bijux-proteomics-core` is still not architectural-ready
- `bijux-proteomics-dev` is still not architectural-ready
- `bijux-proteomics-intelligence` is still not architectural-ready
- `bijux-proteomics-knowledge` is still not architectural-ready
- `bijux-proteomics-lab` is still not architectural-ready
- `bijux-proteomics-runtime` is still not architectural-ready
- `proteomics` is still not architectural-ready
- `proteomics-core` is still not architectural-ready
- `proteomics-foundation` is still not architectural-ready
- `proteomics-intelligence` is still not architectural-ready
- `proteomics-knowledge` is still not architectural-ready
- `proteomics-lab` is still not architectural-ready
- `proteomics-runtime` is still not architectural-ready
- `agentic-proteins` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `bijux-proteomics` still carries reopened completion pressure: docs and tree still contradict each other; historical topology language still dominates current design; root public breadth still exceeds owner logic depth
- `bijux-proteomics-knowledge` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `proteomics` still carries reopened completion pressure: historical topology language still dominates current design; root public breadth still exceeds owner logic depth; root public module count still rivals the package owner-family count
- `proteomics-core` still carries reopened completion pressure: historical topology language still dominates current design; root public breadth still exceeds owner logic depth; root public module count still rivals the package owner-family count
- `proteomics-foundation` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `proteomics-intelligence` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `proteomics-knowledge` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `proteomics-lab` still carries reopened completion pressure: root public breadth still exceeds owner logic depth
- `proteomics-runtime` still carries reopened completion pressure: historical topology language still dominates current design; root public breadth still exceeds owner logic depth; root public module count still rivals the package owner-family count

## Docs failures

These blockers show where public wording, routing, or scrutiny surfaces drift away from the evidence they are supposed to defend.

- `black-box-language-outruns-rerun-evidence`: dda still requests outsider_auditable_bounded but the black-box benchmark dashboard only defends review_grade_bounded
