---
title: Scientific Package Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Scientific package map

The core source tree is grouped by scientific responsibility. Domain modules
own models and algorithms; interface modules assemble those capabilities into
CLI operations and portable artifacts; workflow modules connect validated
steps without moving their scientific ownership.

## From molecules to evidence

### Sequences and experimental context

`sequences` handles FASTA records, validation, decoys, contaminants, digestion,
peptide indexing, and sequence-derived properties. `study` models sample sheets,
design factors, contrasts, feasibility, power, and repair suggestions. `domain`
holds program, target, assay, lifecycle, review, constraint, and semantic-ID
contracts used across workflows.

### Chemistry and signal

`chemistry` owns amino-acid masses, modified-peptide parsing and resolution,
fragment-ion contracts, isotope envelopes, adduct annotation, isotope labeling,
and theoretical references. `io` owns supported file and table boundaries,
including spectra, mzML, chromatography, raw-source lineage, normalized run
bundles, and format conversion.

These layers preserve the difference between a theoretical chemical value, an
instrument observation, and an imported search-engine assertion.

### Identification and protein inference

`identification` normalizes search results from Comet, DIA-NN, FragPipe,
MaxQuant, OpenMS, Sage, and Spectronaut. It owns PSM contracts, score and FDR
review, calibration, contaminant audit, peptide evidence, protein grouping,
parsimony, ambiguity, and inference benchmarks. Adapter-specific information
loss is recorded instead of silently coerced into a richer canonical model.

### Quantification and specialized analysis

`quantification` covers peptide and protein matrices, LFQ, normalization,
missingness, differential analysis, uncertainty, reproducibility, and
provenance. `dia` adds precursor/protein matrices, library coverage, run QC,
and transition QC. `ptm`, `proteoforms`, `multiplex`, `isotope_labeling`, and
`targeted` own their specialized evidence and review semantics.

### Interpretation and review

`interpretation` connects governed quantitative results to contrasts,
pathways, biological context, contaminants, PTMs, and structures. `review`
produces result manifests, evidence cards, explanations, search and query
surfaces, interactive bundles, biological reports, and trust material.
`lab` contains scientific QC and validation-planning contracts that precede the
operational assay ownership of `bijux-proteomics-lab`.

### Benchmarks and workflows

`benchmarks` owns corpora, public case studies, challenge assets, generalization
reports, performance evidence, and flagship acceptance. `workflow` defines
runtime-agnostic requests, validation, scientific gates, report assembly, and
family-specific routes. The workflow layer composes domain owners; it must not
become an alternative location for their algorithms.

## Artifact progression

```mermaid
flowchart TD
    raw["raw or exported input"]
    normalized["normalized scientific contract"]
    reviewed["reviewed evidence with QC"]
    workflow["workflow request and acceptance criteria"]
    bundle["benchmark asset bundle"]
    raw --> normalized --> reviewed --> workflow --> bundle
```

Every progression should retain source lineage, declared normalization,
thresholds, reason codes, and failure state. A downstream summary is not a
replacement for the normalized or reviewed artifact that supports it.

## Extension rules

- Add a new file adapter under the scientific format or identification owner,
  and make information loss explicit.
- Add a new algorithm beside the domain contract it implements, not inside a
  CLI handler or report renderer.
- Add a workflow only after its input, output, failure, and acceptance
  contracts are stable.
- Add a public benchmark only with provenance, licensing, freshness, challenge
  coverage, and family-specific acceptance evidence.
- Keep execution providers, checkpoints, and replay in runtime; keep evidence
  reconciliation and recommendation policy in their owning packages.

For executable entry points, continue with the
[API and CLI surface](../interfaces/api-surface.md). For the evidence boundary,
use [benchmark assets](benchmark-assets.md) and
[flagship acceptance bars](flagship-acceptance-bars.md).
