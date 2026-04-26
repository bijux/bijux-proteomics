---
title: bijux-proteomics-lab
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-lab

`bijux-proteomics-lab` is the assay planning and outcomes package in
`bijux-proteomics`. Start here when the question is about experiment
batch design, dependency scheduling, rerun strategy, or closed-loop
transitions from assay observations into next-cycle planning.

This package turns recommended work into executable assay batches and promotes
observed outcomes back into the next decision cycle.

This package is the planning and feedback hinge between recommendation
logic and the evidence system. It does not decide biological meaning on
its own, and it does not replace runtime execution. It owns the lab-side
questions that sit between those two layers: what to run, in what order,
with which gates, and what to do after the outcome lands.

## What This Package Owns

- experiment planning from candidate pressure, readiness, and review gates
- batch construction, dependency ordering, and material-aware scheduling
- rerun strategy, failure triage, and outcome-to-evidence promotion readiness
- review queues and feedback records that connect lab work to the next cycle

## What This Package Does Not Own

- the upstream recommendation policy that decides scientific priority
- the canonical evidence semantics that knowledge owns after promotion
- the execution control layer that runtime owns while runs are in progress

## Open This Section When

- you need the package entrypoint for planning and assay outcome docs
- you are checking scheduling, readiness, rerun, or promotion decisions
- you want the shortest route into closed-loop lab execution contracts

## Open Another Package When

- the real question is which candidate should be preferred before lab planning
- the real question is how an active run is orchestrated or observed
- the real question is how promoted evidence changes trust or contradiction
  state

## Pages In This Package

- [Foundation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/)
- [Architecture](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/)
- [Interfaces](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/)
- [Operations](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/)
- [Quality](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/quality/)

## Neighboring Packages

- open [bijux-proteomics-intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) when the unresolved question is recommendation policy
- open [bijux-proteomics-knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/) when the unresolved question is evidence or contradiction state after an assay
- open [bijux-proteomics-runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
  when the unresolved question is run orchestration, operator entrypoints, or
  runtime artifacts
- stay here when the real concern is how work is scheduled, rerun, or promoted after execution

## Concrete Anchors

- `packages/bijux-proteomics-lab` for the package root
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py` for
  plan, schedule, and review-packet ownership
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py` for
  outcome, rerun, and promotion-readiness ownership
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py` for
  queue and feedback persistence contracts
- `packages/bijux-proteomics-lab/tests` for planning and outcome proof

## Bottom Line

Open this page when the question is how proteomics work crosses the line from
recommended to executable, and how assay results re-enter the next cycle. If
the question is really about meaning before planning or meaning after
promotion, a neighboring package owns it.
