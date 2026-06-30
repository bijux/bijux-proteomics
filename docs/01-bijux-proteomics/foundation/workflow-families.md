---
title: Workflow Families
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-01
---

# Workflow Families

This page is the fastest route from a workflow-family label to the sentence the
repository can honestly publish today.

The family table is not a marketing summary. It is the place where scientific
breadth, runtime realism, grounding pressure, and downstream consequence are
collapsed into one bounded family call.

## How To Read The Table

- `public posture` tells you the strongest sentence the repository can publish
  today for that family
- `runtime lane` tells you whether the strongest current route is
  `raw_executable` or still `import_only`
- `evidence root` tells you where a serious reviewer should start
- `main limiter` tells you why stronger language is still blocked

## Family Comparison

| family | public posture | runtime lane | evidence root | main limiter |
| --- | --- | --- | --- | --- |
| `dda` | outsider-auditable, bounded | `import_only` | [DDA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dda-benchmark-lineage/) | in-repo live-engine parity still remains weaker than the reviewed downstream path |
| `dia` | outsider-auditable, bounded | `raw_executable` | [DIA Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/dia-benchmark-lineage/) | library incompleteness and downstream absent-peptide consequence still narrow the broader sentence |
| `lfq` | review-grade, bounded | `raw_executable` | [LFQ Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/lfq-benchmark-lineage/) | missingness, normalization pressure, and external-review-kit limits still block outsider-auditable release language |
| `multiplex` | internal support only | `raw_executable` | [Multiplex Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/multiplex-benchmark-lineage/) | the current stress package still collapses outsider-facing trust |
| `ptm` | outsider-auditable, bounded | `raw_executable` | [PTM Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ptm-benchmark-lineage/) | localization evidence is stronger than downstream consequence confidence |
| `targeted` | outsider-auditable, bounded | `raw_executable` | [Targeted Benchmark Lineage](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/targeted-benchmark-lineage/) | calibration, interference, and assay-burden pressure still block broader certainty |

## Why The Families Are Substantively Stronger Now

The family labels now sit on top of deeper package substance than they did at
`v0.3.7`:

- `core` carries broader sequence, chemistry, spectra, mzML, DIA, PTM, and
  quantification surfaces
- `runtime` carries replay, rerun, refusal, and artifact-integrity routes
- `knowledge` carries workflow-level claim grounding and contradiction review
- `intelligence` carries recommendation challenge, downgrade, and regret
  surfaces
- `lab` carries control demand, refusal, and requested-versus-observed outcome
  loops

That deeper product is exactly why the family calls have to stay explicit.
More real substance makes overclaiming easier if the limiter is not named.

## What The Family Calls Refuse To Hide

- a strong benchmark package does not erase runtime weakness
- a reproducible rerun lane does not erase grounding or consequence weakness
- a strong recommendation packet does not erase assay-burden pressure
- one strong family packet does not authorize broader repository-wide language

## Best Next Questions

- Open [Flagship Release Candidate](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/flagship-release-candidate/)
  when the question is how the current family calls combine into one release
  bundle.
- Open [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when the question is whether the public evidence root is broad enough and
  honest enough.
- Open [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  when the question is whether the runtime lane still deserves the published
  sentence.
- Open [Decision Support](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/decision-support/)
  when the question is whether grounding, recommendation posture, or lab burden
  is the real limiter.

## Reader Rule

If the family table sounds stronger than the family-specific trust page, rerun
surface, or consequence route, the table is wrong and must narrow.

## Boundary

This page compares family-level public posture. It should hand the reader to
the evidence, runtime, grounding, recommendation, or lab owner once the real
question is known.
