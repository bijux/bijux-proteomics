---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-01
---

# Package Overview

`bijux-proteomics-core` owns the durable scientific contracts that the rest of
the repository depends on: program, target, assay, and review entities;
lifecycle transitions; review gates; normalized proteomics I/O seams; and
benchmark-acceptance surfaces. The package is only healthy when those
scientific rules remain runtime-agnostic and distinct from evidence memory,
recommendation posture, and assay consequence.

This package is materially broader now than older overview pages implied. It is
not only a workflow-contract layer. It owns a substantial scientific surface
across sequence handling, chemistry, spectra and mzML intake, identification,
quantification, PTM review, DIA support, benchmark assets, review artifacts,
and workflow planning.

## Why This Package Feels Bigger Now

- chemistry, mass calculation, modification, fragment, and isotope work now
  sit in the same product story as workflow contracts and benchmark review
  surfaces
- benchmark packages, lineage roots, challenge corpora, and acceptance bars
  are part of core scientific law rather than downstream decoration
- readers can now inspect more of the real scientific machinery directly
  instead of inferring it from runtime, reports, or recommendation summaries

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
- encode lifecycle transitions, benchmark-acceptance bars, gate truth, and
  runtime-agnostic workflow contracts
- publish benchmark and scientific contract surfaces to downstream packages

## What Readers Commonly Underestimate

- this package owns the repository's cleanest chemistry and assay semantics,
  not only its workflow grammar
- this package decides which benchmark evidence roots are structured enough to
  become public flagship surfaces
- this package is where biological and analytical packages inherit durable
  reviewable inputs instead of inventing them ad hoc

## What It Refuses

- shared schema primitives that belong in foundation
- evidence memory, contradiction handling, or recommendation posture
- operator-facing runtime execution, replay, or assay-consequence ownership

## Strongest First Checks

- open the public package roots and benchmark catalog when you need the
  shortest proof that the package owns real sequence, chemistry, review, and
  workflow surfaces
- open the benchmark asset handbook when the question is whether a workflow
  claim starts from enough public evidence
- open runtime, knowledge, intelligence, or lab only after the core scientific
  contract is clear enough to execute or judge honestly

## Best Reader Route

- start here when the question is whether `bijux-proteomics` has real
  scientific depth or only governance around smaller utilities
- continue to [Flagship Public Benchmark Catalog](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/flagship-public-benchmark-catalog/)
  when you need the paired public evidence roots that make the contracts
  inspectable
- continue to [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when you need freshness, lineage, licensing, incompleteness, and acceptance
  context

## First Proof Check

- `packages/bijux-proteomics-core/src/bijux_proteomics`
- `packages/bijux-proteomics-core/tests`
- benchmark package manifests, asset roots, and acceptance-facing evidence
- neighboring handbook branches once a change crosses the local role
