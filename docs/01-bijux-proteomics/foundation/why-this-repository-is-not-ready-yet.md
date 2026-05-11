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

- blocked release bars: 2
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
