---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-06-30
---

# Package Overview

`bijux-proteomics-core` owns the durable scientific contracts that the rest of
the repository depends on: program, target, assay, and review entities;
lifecycle transitions; review gates; normalized proteomics I/O seams; and
benchmark-acceptance surfaces. The package is only healthy when those
scientific rules remain runtime-agnostic and distinct from evidence memory,
recommendation posture, and assay consequence.

This package is materially broader now than older overview pages implied. It is
not only a small workflow-contract layer. It owns a substantial scientific
surface across sequence handling, chemistry, spectra and mzML intake,
identification, quantification, PTM review, DIA support, benchmark assets,
review artifacts, and workflow planning.

## Concrete Scientific Families

- sequence and study contracts under `domain`, `sequences`, and `study`
- chemistry, isotopes, modifications, fragments, and mass calculations under
  `chemistry`
- normalized proteomics I/O for formats, spectra, raw-source adapters, and
  chromatography under `io`
- identification and reviewable search normalization under `identification`
- label-free quantification, missingness, normalization, provenance, and
  statistical surfaces under `quantification`
- PTM, proteoform, targeted, DIA, and interpretation surfaces that stay
  package-owned instead of being hidden in notebooks or report glue
- benchmark package ownership and flagship workflow contracts under
  `benchmarks` and `workflow`

## Why That Depth Matters

- runtime can execute and replay workflows without redefining scientific truth
- knowledge can ground claims against richer, typed upstream evidence
- intelligence can rank or downgrade based on explicit scientific artifacts
  instead of presentation-only summaries
- lab can inherit assay-facing consequence from stable review and workflow
  contracts rather than reverse-engineering ad hoc outputs

## What It Owns

- define program, target, assay, and review entities
- encode lifecycle transitions, gate truth, and runtime-agnostic workflow
  requests
- publish benchmark-acceptance and scientific contract surfaces to downstream
  packages

## What It Refuses

- shared schema primitives that belong in foundation
- evidence memory, contradiction handling, or recommendation policy
- operator-facing runtime execution, replay, or assay-consequence ownership

## Strongest First Checks

- open the public root package and README examples when you need the shortest
  proof that the package owns real sequence, chemistry, review, and workflow
  surfaces
- open the benchmark asset handbook when the question is whether a workflow
  claim starts from enough public evidence
- open the runtime handbook only after the core scientific contract is clear
  enough to execute honestly

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- neighboring handbook branches once a change crosses the local role
