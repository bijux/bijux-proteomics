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

- there is still no single end-to-end proteomics workflow that runs from
  sequence intake through evidence review, advancement decisions, and
  wet-lab follow-up with one gold-standard proof bundle
- several workflow families are benchmark-backed at the reviewed-artifact level
  without being raw-to-result reproducible inside this repository
- release-facing benchmark discipline is stronger than before, but some
  scientific surfaces are still governed more by bounded refusal and caveat
  than by full positive support

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

- runtime end-to-end proof is still stronger for governed replay and reviewable
  artifacts than for one flagship scientific workflow that spans the whole
  package family
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

## Boundary

This page is not a product roadmap. It is the current honesty boundary for the
repository.
