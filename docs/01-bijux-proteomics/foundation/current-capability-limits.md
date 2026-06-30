---
title: Current Capability Limits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Current Capability Limits

This page names what `bijux-proteomics` still cannot do, only does partially,
or can describe more easily than it can prove.

It exists so repository releases, handbook pages, and package-level claims can
point to one exact limits surface instead of letting each package describe
scope drift differently.

## Repository-Wide Limits

Outsider-auditable workflow families today: `dda`, `dia`, `ptm`, `targeted`.
Review-grade-bounded workflow families today: `lfq`.
Internal-support-only workflow families today: `multiplex`.

- several workflow families are now outsider-auditable in a bounded sense, but
  there is still no broad cross-family proteomics proof set that survives the
  same standard with supported comparator posture and decision-grade
  consequence
- LFQ remains review-grade bounded because its current external review kit and
  acceptance surface still narrow the stronger outsider-facing sentence
- PTM and targeted remain bounded because their shared consequence chain still
  ends at exploratory-only follow-up, and one doubled assay burden can still
  collapse the recommendation back toward refusal
- DDA still stops short of in-repo live-engine rerun parity
- multiplex still remains internal support only, so no release language should
  let it ride for free on adjacent flagship trust claims

## Scientific Limits

- reviewed benchmark packages still do not mean universal transfer across
  instrument classes, sample complexity, or study design
- some PTM, glycopeptide, and advanced protein-inference surfaces still stop at
  explicit refusal or bounded partial support rather than full scientific
  coverage
- batch-effect, interpretation, and downstream recommendation surfaces remain
  more trustworthy when treated as review aids than as autonomous scientific
  conclusions

## Execution Limits

- runtime end-to-end proof is now real across DIA, LFQ, multiplex, PTM, and
  targeted review lanes, but DDA still stops at import-backed runtime proof and
  every family remains bounded by narrower claim scope than a broad production
  workflow promise
- compatibility remains intentionally visible through `agentic-proteins`; the
  migration is controlled, but the compatibility bridge still exists
- provider and execution realism still depend on a narrower set of validated
  pathways than the package map alone might suggest

## Documentation Rule

- if a repository, package, or release note sounds more capable than this page,
  the wording is wrong until the code, tests, artifacts, and scientific proof
  move first
- if a real capability lands and this page is stale, update this page in the
  same change set as the new proof
- open `docs/01-bijux-proteomics/foundation/workflow-consequence-maps.md` and
  `docs/01-bijux-proteomics/foundation/what-changed-the-recommendation.md`
  before widening
  LFQ, PTM, or targeted language from bounded recommendation toward
  decision-grade claims

## Boundary

This page is not a product roadmap. It is the current honesty boundary for the
repository.
