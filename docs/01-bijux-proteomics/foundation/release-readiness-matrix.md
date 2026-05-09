---
title: Release Readiness Matrix
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-09
---

# Release Readiness Matrix

This repository does not earn stronger release language by collecting more
governance prose. It earns stronger language only when a hostile reviewer can
challenge the product across a small set of decisive categories and the checked
evidence survives.

The machine-readable matrix lives in
`configs/package-governance/release-readiness-matrix.toml`. It is generated
from live package-boundary, workflow, runtime, evidence, and consequence
validators so the root wording cannot drift ahead of the actual repository.

## Matrix Categories

| Category | What it asks | Primary evidence |
| --- | --- | --- |
| Workflow-family product evidence | Does the root promise stay behind the checked workflow manifest and package-family readiness evidence? | canonical workflow manifest, release family manifest, product architecture |
| Black-box rerunability | Can an outsider challenge the flagship runtime lane without maintainers narrating around missing artifacts? | runtime execution boundary, black-box run verification, flagship release candidate, public artifact index |
| Benchmark asset quality | Are benchmark-backed claims grounded by the release dossier and workflow claim checks? | scientific release manifest, benchmark asset docs, claim grounding checks |
| Docs clarity | Do root docs route readers to real evidence without stronger trust language than the evidence supports? | README, docs home, product architecture, cross-package ownership |
| Package-boundary stability | Do dependency directions, public imports, and package README routing still describe the same owner model? | package dependency policy, repository product shape, cross-package ownership |
| Artifact hygiene | Does the repo stay free of cache spillover, package-local artifact roots, and duplicate owner surfaces on disk? | repository file ownership matrix, drift audit, artifact governance |
| Consequence realism | Does recommendation posture stay behind the weakest downstream lab consequence boundary? | intelligence confidence docs, lab docs, capability limits |

## Current Use

Use this page when someone asks whether the repository is ready for stronger
public claims. The answer should begin with the matrix categories above, not
with badges, package count, or handbook volume.

## First Proof Check

- `configs/package-governance/release-readiness-matrix.toml`
- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/release/governance/release_readiness_matrix.py`
- `README.md`

## Design Pressure

The easy failure is to describe readiness in broad adjectives while the real
review blockers still live in scattered validators. The matrix exists so the
blockers stay small, named, and hard to soften.
