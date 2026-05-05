# Experiment Design And Protocol Planning

`bijux-proteomics-lab` now includes a typed experiment-design surface for
turning sample metadata and design tables into reviewable execution plans.

This layer sits above `bijux-proteomics-core` design parsing. It does not own
file-format validation itself. It consumes normalized `ExperimentalDesignEntry`
records and returns deterministic planning artifacts for lab operators and
review workflows.

## Surface overview

The design surface currently covers:

- sample-preparation metadata
- instrument-method metadata
- experiment design validation with valid and rejected contrasts
- two-condition power-analysis advisories
- deterministic run-order randomization
- fractionation plans
- multiplex channel planning
- spike-in and QC insertion planning
- carryover risk advisories
- bundled protocol evidence payloads

## Core contracts

### Metadata

- `SamplePreparationMetadata`
- `InstrumentMethodMetadata`

These models capture the execution context that usually gets lost in ad hoc
notes:

- digestion protocol
- cleanup strategy
- fractionation strategy
- labeling strategy
- enrichment strategy
- instrument and acquisition mode
- gradient length
- resolution and collision settings

### Design validation

`validate_experiment_design(...)` checks:

- condition count
- pairwise contrast validity
- replicate sufficiency
- batch confounding
- duplicate sample/fraction rows
- samples that span multiple batches

The result is an `ExperimentDesignValidationReport` with both valid and
rejected contrasts plus explicit issues.

### Power advisory

`build_power_analysis_advisory(...)` provides a deterministic, clearly marked
advisory estimate for a two-condition comparison. It reports:

- current replicate counts
- target power
- alpha
- standardized effect size
- estimated current power
- recommended replicates per condition

This is intentionally lightweight. It is a planning advisory, not a substitute
for a full statistical consulting workflow.

### Randomization and run order

`plan_batch_randomization(...)` creates a deterministic order from normalized
design entries. The current algorithm spreads conditions within each batch as
evenly as it can while preserving a stable seed-driven output.

`plan_spike_in_qc_samples(...)` then inserts:

- periodic QC pools
- optional spike-in standards

over a base run order.

### Fractionation and multiplex planning

`build_fractionation_plan(...)` links samples and fractions to stable run
labels.

`plan_multiplex_labeling(...)` assigns samples to channels while allowing
explicit reserved channels for:

- pooled reference material
- QC bridge channels

The plan reports whether the resulting condition distribution is balanced.

### Carryover and protocol evidence

`assess_carryover_risk(...)` flags risky transitions such as:

- high abundance to low abundance
- high abundance to blank

`build_lab_protocol_evidence_bundle(...)` combines protocol metadata and plan
artifacts into one reviewable payload that can travel into lab execution or
review queues.

## Typical flow

```python
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics_lab import (
    build_fractionation_plan,
    plan_batch_randomization,
    validate_experiment_design,
)
```

Typical sequence:

1. Parse a design table in `bijux-proteomics-core`.
2. Validate design structure and contrast readiness.
3. Create randomized run order.
4. Build fractionation and multiplex plans if relevant.
5. Insert QC and spike-in controls.
6. Review carryover advisory.
7. Bundle protocol evidence for operator use.

## Current limits

This iteration is deliberately serious but bounded.

What it does well now:

- deterministic, typed planning artifacts
- batch-confounding and replicate-readiness checks
- reproducible run-order planning
- explicit protocol metadata instead of free text
- clear protocol evidence bundling

What is still left:

- paired and multifactor design reasoning
- instrument-vendor-specific method validation
- richer carryover models driven by observed abundance or wash history
- TMT balancing beyond one plex at a time
- automated power estimation across more complex statistical models
- live operator entrypoints and report renderers
