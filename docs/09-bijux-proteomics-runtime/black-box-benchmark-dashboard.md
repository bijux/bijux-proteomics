---
title: Black-Box Benchmark Dashboard
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Black-Box Benchmark Dashboard

This dashboard states what the runtime and public benchmark evidence can defend
without maintainer narration. It lists every workflow family by current public
language, black-box-allowed language, run mode, drift visibility, artifact
completeness, and remaining rerun blockers.

Its job is narrower than the full repository trust call. This page asks: if an
outsider is only allowed to inspect tracked benchmark packages and runtime
artifacts, which sentence survives? That makes it a runtime-and-evidence
boundary page, not the final scientific or recommendation verdict.

This distinction matters because the repository is now deeper than a simple
execution story. Several workflow families have meaningful scientific breadth,
but this dashboard deliberately asks a harsher question: what can an
independent reviewer defend from the shipped package and checked runtime lane
alone?

## How To Read This Dashboard

- `requested language` is the sentence the broader repository route would like
  to defend
- `allowed language` is the sentence the black-box runtime and benchmark packet
  can defend without extra maintainer explanation
- a downgrade from requested to allowed language is not a failure of the page;
  it is the point of the page
- `artifact completeness` says whether the packet is present enough to inspect,
  not whether the scientific claim is fully generalized
- `drift status` is operationally important because a family can be honest,
  complete, and still remain fragile when replay pressure widens

| workflow family | requested language | allowed language | primary run mode | companion run mode | drift status | artifact completeness |
| --- | --- | --- | --- | --- | --- | --- |
| `dda` | `outsider_auditable_bounded` | `review_grade_bounded` | `import_only` | `import_only` | `highly_stable` | `complete` |
| `dia` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `lfq` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `multiplex` | `internal_support_only` | `internal_support_only` | `raw_executable` | `raw_executable` | `fragile_transfer` | `complete` |
| `ptm` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |
| `targeted` | `outsider_auditable_bounded` | `outsider_auditable_bounded` | `raw_executable` | `raw_executable` | `highly_stable` | `complete` |

## Why The Families Diverge Here

- `dda` still drops from requested to allowed language because import-backed
  review remains the strongest independently inspectable lane
- `multiplex` proves that complete raw-executable packets are not enough when
  downstream challenge, consequence, and outsider-facing trust routes remain
  narrower
- `dia`, `lfq`, `ptm`, and `targeted` keep stronger allowed language because
  their checked runtime bundles, companion packages, and benchmark packets now
  survive the black-box question more cleanly

## What This Dashboard Proves

- DIA, PTM, targeted, and LFQ now have runtime-and-benchmark packets strong
  enough to survive black-box outsider inspection
- DDA still downgrades here because import-backed execution remains visible
  even though the broader family packet is scientifically meaningful
- multiplex can be real, complete, and raw-executable while still remaining
  internal support only

## What This Dashboard Does Not Prove

- it does not authorize broader biological or recommendation claims on its own
- it does not erase vendor-parity, generalization, or lab-consequence limits
- it does not turn runtime completeness into universal scientific confidence

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
- no multiplex lab packet or outsider decision brief family
- multiplex authority is intentionally kept out of the outsider-facing flagship set

### `ptm`

- occupancy and regulatory interpretation still remain narrower than localization evidence
- PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning

### `targeted`

- vendor-parity and calibration-clean authority are still outside the current proof boundary
- targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty

## Reading Discipline

- start here when you need the strongest outsider-facing sentence the runtime
  lane can defend
- drop to the rerun kits and black-box verification pages when the reviewer
  needs exact opening order rather than family summary
- hand off to workflow families, decision support, or lab consequence only
  after the runtime limit has been named explicitly

## Best Next Routes

Open [Workflow Families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
when the next question is how this runtime view changes the released family
sentence.

Open [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
when the next question is whether the public evidence root itself is broad
enough and honest enough.

Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
when the next question is whether grounding, recommendation posture, or lab
consequence still narrows the final call.
