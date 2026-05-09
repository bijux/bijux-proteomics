---
title: Black-Box Benchmark Dashboard
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-09
---

# Black-Box Benchmark Dashboard

This dashboard states what the runtime and public benchmark evidence can defend without maintainer narration. It lists every workflow family by current public language, black-box-allowed language, run mode, drift visibility, artifact completeness, and remaining rerun blockers.

| workflow family | requested language | allowed language | primary run mode | companion run mode | drift status | artifact completeness |
| --- | --- | --- | --- | --- | --- | --- |
| `dda` | `outsider_auditable_bounded` | `review_grade_bounded` | `import_only` | `import_only` | `highly_stable` | `complete` |
| `dia` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `lfq` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `multiplex` | `internal_support_only` | `internal_support_only` | `raw_executable` | `raw_executable` | `fragile_transfer` | `complete` |
| `ptm` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `targeted` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |

## Remaining Independent-Rerun Blockers

### `dda`

- primary flagship lane is still not raw-executable in the runtime layer
- companion generalization lane is still not raw-executable in the runtime layer
- no in-repo live-engine rerun parity
- one-run package cannot authorize broad production-cohort DDA claims

### `dia`

- no chromatogram-level vendor parity
- library incompleteness and absent-peptide consequences still block broader biological confidence

### `lfq`

- no stronger public truth package for accuracy beyond repeatability
- generalization beyond the current cohort package remains explicitly bounded

### `multiplex`

- 1 cross-package claim(s) collapse under the companion rerun path
- no multiplex lab packet or outsider review packet family
- multiplex authority is intentionally kept out of the outsider-facing flagship set

### `ptm`

- occupancy and regulatory interpretation still remain narrower than localization evidence
- PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning

### `targeted`

- vendor-parity and calibration-clean authority are still outside the current proof boundary
- targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty
