# Proteomics Interpretation Workflows

`interpretation/runs.py`, `interpretation/quantitative.py`,
`interpretation/ptm.py`, `interpretation/contaminants.py`,
`interpretation/contrasts.py`, `interpretation/pathways.py`, and
`interpretation/structures.py` own the interpretation family for
`bijux-proteomics-intelligence`. They turn already-typed proteomics evidence
into reviewable summaries, but they must stay explicit about what they can
decide and what they must refuse to overclaim.

## What this surface can decide

- whether a run is interpretation-ready enough to summarize
- which significant differential signals deserve cautious summary treatment
- which PTM, contamination, missingness, and enrichment signals deserve
  advisory attention
- which caveats must remain attached to interpretation outputs

## What this surface must refuse or downgrade

- mechanistic certainty without convergent contradiction-free support
- causal claims from descriptive enrichment alone
- paired-design, multifactor, or permutation-calibrated claims that the current
  typed inputs do not support
- definitive instrument diagnosis from QC-derived artifact summaries

## Core inputs

Interpretation functions consume stable core-owned outputs, especially:

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
from bijux_proteomics_intelligence.interpretation.runs import (
    build_run_interpretation_summary,
)
from bijux_proteomics_intelligence.interpretation.quantitative import (
    interpret_differential_abundance,
)

summary = build_run_interpretation_summary(...)
report = interpret_differential_abundance(...)
```

In practice:

1. Build QC, quantification, PTM, or differential evidence in
   `bijux-proteomics-core`.
2. Normalize protein-to-theme annotations into
   `ProteinAnnotationAssignment` records.
3. Run the relevant `interpretation` owner module.
4. Persist or render the returned typed report without re-inferring meaning in
   downstream code.

## Run summaries

`build_run_interpretation_summary(...)` produces a compact run view with:

- run, sample, and condition identity
- spectrum, identified-spectrum, PSM, and quantified-entity counts
- QC-blocked state
- explicit interpretation signals such as `identification-ready`,
  `quant-available`, `contaminant-pressure`, and `qc-blocked`

Use it when an operator or higher-level service needs a one-screen view of
whether a run is ready for cautious biological interpretation.

## Differential interpretation

`interpret_differential_abundance(...)` consumes a typed differential report and
returns:

- top significant upregulated entities
- top significant downregulated entities
- enriched terms over significant entities
- theme summaries
- statistical provenance including normalization method, entity level, and
  tested and significant counts

This path is intentionally conservative. It should downgrade broad biological
claims when the significant set is thin or when contradictory evidence posture
would make overclaim misleading.

## PTM and artifact interpretation

`interpret_ptm_sites(...)` from `interpretation/ptm.py` works over accepted
site-level evidence and combines:

- accepted site status from `PtmSiteFdrReport`
- motif windows
- occupancy shifts
- advisory kinase and pathway terms from annotations

`interpret_contaminant_artifacts(...)` from `interpretation/contaminants.py`
turns QC metrics into explicit findings such as contaminant burden, digestion
specificity loss, mass calibration drift, and low identification rate.

Both outputs are reviewable advisory surfaces. They do not replace raw-spectrum
rescoring, localization probability modeling, or instrument remediation logic.

## Contrast recommendation, missingness, and enrichment

`recommend_experimental_contrasts(...)` from `interpretation/contrasts.py`
checks whether a design is suitable for pairwise interpretation by looking at
condition count, replicate count, and batch overlap.

`analyze_missingness_patterns(...)` from `interpretation/quantitative.py`
classifies quant entities into advisory labels such as `mostly_observed`,
`filter_dominated`, `condition_linked_missingness`, `mnar_like_low_signal`,
`mar_like_random`, and `mixed`.

`compute_protein_set_enrichment(...)`, `compute_ranked_enrichment(...)`, and
`extract_biological_themes(...)` from `interpretation/pathways.py` provide
deterministic enrichment summaries and readable pathway themes.

These helpers must keep caveats explicit. They do not establish causal pathway
truth, empirical GSEA significance, or multifactor statistical law.

## Deliberate limits

- enrichment does not expose permutation-calibrated NES or empirical significance
- contaminant intelligence is not instrument-vendor specific
- contrast recommendations do not cover paired or multifactor models
- missingness analysis is heuristic and advisory
- PTM interpretation does not rescore raw spectra

Those limits are deliberate. This band owns typed interpretation contracts, not
the deeper inference layers that would make those stronger claims defensible.
