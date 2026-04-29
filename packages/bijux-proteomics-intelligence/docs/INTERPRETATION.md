# Proteomics Interpretation Workflows

`bijux-proteomics-intelligence` now includes an interpretation layer for
turning typed proteomics evidence into reviewable biological summaries.

These contracts sit above `bijux-proteomics-core`. They do not recompute raw
search, quantification, PTM localization, or QC evidence. They consume those
typed outputs and produce deterministic interpretation artifacts.

## What this surface owns

- run-level interpretation summaries over QC and quant availability
- differential-abundance interpretation with typed provenance
- PTM site interpretation over accepted sites, motifs, occupancy, and advisory
  annotation terms
- contaminant and artifact intelligence over QC metrics
- experimental contrast recommendations from design metadata
- missingness pattern analysis over quant tables
- outlier sample explanations from batch QC and replicate correlations
- overrepresentation enrichment and ranked enrichment
- biological theme extraction from protein annotations

## What it does not own

- raw PSM parsing, quantification, PTM mapping, or QC metric generation
- external ontology downloads or live knowledge graph queries
- permutation-based GSEA significance calibration
- multifactor statistical modeling or paired-design differential inference
- vendor-specific contaminant heuristics or instrument remediation logic

## Core inputs

The interpretation functions are designed to consume stable outputs from
`bijux-proteomics-core`, especially:

- `LcmsRunQcReport`
- `QcRunAssessmentReport`
- `LabelFreeQuantTable`
- `DifferentialAbundanceReport`
- `PtmSiteEntry`
- `PtmSiteFdrReport`
- `PtmMotifWindow`
- `PtmOccupancyEntry`
- `InstrumentBatchQcReport`
- `ReplicateCorrelationReport`
- `ExperimentalDesignEntry`

Protein annotations are carried through the local
`ProteinAnnotationAssignment` model so interpretation remains deterministic and
testable without binding the package to one external annotation source.

## Typical flow

```python
from bijux_proteomics_intelligence import (
    ProteinAnnotationAssignment,
    build_run_interpretation_summary,
    compute_protein_set_enrichment,
    interpret_differential_abundance,
)
```

In practice:

1. Build QC, quantification, PTM, or differential evidence in
   `bijux-proteomics-core`.
2. Normalize protein-to-theme annotations into
   `ProteinAnnotationAssignment` records.
3. Run the relevant interpretation helper.
4. Persist or render the returned typed report without re-inferring meaning in
   downstream code.

## Run summaries

`build_run_interpretation_summary(...)` produces a compact run view with:

- run, sample, and condition identity
- spectrum, identified-spectrum, PSM, and quantified-entity counts
- QC-blocked state
- major interpretation signals such as:
  - `identification-ready`
  - `quant-available`
  - `contaminant-pressure`
  - `qc-blocked`

Use it when an operator or higher-level service needs a one-screen view of
whether a run is ready for biological interpretation.

## Differential interpretation

`interpret_differential_abundance(...)` consumes a typed differential report and
returns:

- top significant upregulated entities
- top significant downregulated entities
- enriched terms over significant entities
- theme summaries
- statistical provenance including normalization method, entity level, and
  tested/significant counts

This is intentionally conservative. Only statistically significant entities are
used for the interpretation slice. If a fixture has one significant protein,
the output reflects that rather than inventing symmetry.

## PTM interpretation

`interpret_ptm_sites(...)` works over accepted site-level evidence and combines:

- accepted site status from `PtmSiteFdrReport`
- motif windows
- occupancy shifts
- advisory kinase and pathway terms from annotations

The output is useful for reviewable PTM summaries, but it does not replace
spectrum-level rescoring or localization probability modeling.

## QC-derived artifact intelligence

`interpret_contaminant_artifacts(...)` turns QC metrics into explicit findings
such as:

- contaminant burden
- digestion specificity loss
- mass calibration drift
- low identification rate

This is a rules-based intelligence layer. It is meant to explain likely causes
and operator next steps, not to claim definitive instrument diagnosis.

## Contrast recommendation and missingness

`recommend_experimental_contrasts(...)` checks whether a design is suitable for
pairwise interpretation by looking at:

- condition count
- replicate count
- batch overlap

`analyze_missingness_patterns(...)` classifies quant entities into advisory
labels such as:

- `mostly_observed`
- `filter_dominated`
- `condition_linked_missingness`
- `mnar_like_low_signal`
- `mar_like_random`
- `mixed`

The goal is triage and explainability, not a full missing-data statistical
model.

## Enrichment and themes

Two enrichment paths are available:

- `compute_protein_set_enrichment(...)`
  - hypergeometric upper-tail overrepresentation
  - BH-adjusted p-values
- `compute_ranked_enrichment(...)`
  - deterministic GSEA-style running-sum enrichment
  - enrichment direction and leading edge

`extract_biological_themes(...)` is a presentation-oriented helper built on the
overrepresentation engine.

## Boundaries and next work

Current limits are explicit:

- enrichment does not yet expose permutation-calibrated NES or empirical
  significance
- contaminant intelligence is not instrument-vendor specific
- contrast recommendations do not yet cover paired or multifactor models
- missingness analysis is heuristic and advisory
- PTM interpretation does not yet rescore raw spectra

Those limits are deliberate. The package is now responsible for typed
interpretation contracts, not for pretending those deeper inference layers are
already solved.
