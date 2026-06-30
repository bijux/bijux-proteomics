---
title: Why This Repository Is Not Ready Yet
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Why This Repository Is Not Ready Yet

This page is generated from the current release-readiness matrix. It exists so blocked release bars stay visible in plain language and cannot be softened manually.

It is important to read this as a blocker ledger, not as a claim that the
repository lacks meaningful product depth. The current code, benchmark,
runtime, grounding, recommendation, and consequence surfaces are far stronger
than older docs suggested. This page exists because those stronger surfaces
still do not close every release bar.

- blocked release bars: 3
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

Why this still blocks release language:

- rerun realism is one of the easiest surfaces for readers to overread once the
  runtime docs become stronger
- if the runtime lane still narrows, the root sentence must narrow with it

## Benchmark asset quality

Release claims must stay behind the benchmark asset coverage, grounding, and scientific release evidence actually checked in.

Evidence paths:
- `configs/package-governance/scientific-release-workflows.toml`
- `docs/04-bijux-proteomics-core/foundation/benchmark-freshness-review.md`
- `docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md`
- `docs/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog.md`

Current blockers:
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditEntry' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditReport' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: duplicate-model-ownership: structured model 'BeliefAuditSummary' is owned by multiple canonical packages: bijux-proteomics-core:bijux_proteomics/review/belief/belief_audit_models.py, bijux-proteomics-intelligence:bijux_proteomics_intelligence/belief_audit.py
- `ssot-readiness-blocked`: scientific release dossier is blocked until SSOT readiness is clean: package-substance: bijux-proteomics-core exposes 133 thin modules and needs tighter ownership boundaries

Why this still blocks release language:

- stronger benchmark coverage is not enough if the scientific release dossier
  still exposes ownership duplication or thin-core boundary debt
- root release language cannot outrun the evidence dossier that is supposed to
  defend it

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

Why this still blocks release language:

- docs are now good enough to sound convincing, so they must also be precise
  enough to stop one stronger page from overruling a narrower evidence surface
- root wording is part of release evidence now, not a neutral wrapper around it

## Strongest Companion Routes

- [Release Readiness Matrix](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/)
  for the category view
- [What Would Make This Repository Ready](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-would-make-this-repository-ready/)
  for the exact closure conditions
- [Hostile Review Kit](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/hostile-review-kit/)
  for the whole-repository challenge route that should hit these blockers
