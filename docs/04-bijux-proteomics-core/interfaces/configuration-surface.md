---
title: Scientific Configuration
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Scientific configuration

Core has no process-wide settings object and does not read scientific policy
from ambient environment variables. Configuration is explicit at three
levels: program intent, workflow dispatch, and operation-specific policy. This
makes the assumptions behind a result serializable and reviewable.

## Program intent

`ProgramSpec` records the scientific question before an analysis is selected.
It combines the protein target, mechanism hypothesis, intervention goal,
constraints, liabilities, success criteria, assay requirements, review gates,
evidence needs, operating model, and document provenance. Unknown fields are
rejected.

Stage is not a cosmetic label. `assess_stage_eligibility()` checks the
requirements of review, lab-ready, and learning states and returns explicit
blockers. `revise_program()` increments the document revision and hashes the
program summary so that a changed decision context is visible.

## Workflow dispatch

Typed workflow models select an end-to-end analysis family:

| Configuration | Input and decision boundary |
| --- | --- |
| `LabelFreeWorkflowConfig` | Feature intensities, design, FASTA, rollup, normalization, and biological selection |
| `DdaWorkflowConfig` | Generic or FragPipe PSMs, adapter dialect, FDR, parsimony, rollup, and normalization |
| `DiannWorkflowConfig` | DIA-NN results, peptide and protein-group policy, q-value threshold, and normalization |
| `MaxquantWorkflowConfig` | MaxQuant evidence, peptides, protein groups, design, and LFQ acceptance policy |
| `TmtWorkflowConfig` | Reporter-channel mapping, control channel, channel normalization, and design covariates |
| `SilacWorkflowConfig` | SILAC column mapping, ratio policy, normalization, and paired design fields |
| `PtmWorkflowConfig` | Localization mapping, ambiguity policy, protein correction, motif, and enrichment thresholds |
| `TargetedWorkflowConfig` | Matrix, assay-QC, or validation stage with discovery claims and reliability thresholds |

Each model rejects unknown keys and carries its own `mode`, preventing a
configuration for one acquisition family from being silently dispatched as
another. `output_dir` is shared placement policy; it does not change scientific
meaning.

## Operation policies

Lower-level operations use narrow policy objects next to the calculation they
govern. Important examples include `DigestPolicy`, `FdrPolicy`,
`PeakNormalizationPolicy`, `DifferentialReplicatePolicy`,
`PairedDifferentialPolicy`, `TimeCourseTestingPolicy`,
`MissingValueSummaryPolicy`, and `PtmEvidenceCardPolicy`.

Keep these rules explicit in code or a validated serialized model:

- score orientation and target-decoy labeling;
- q-value and adjusted-p-value thresholds;
- shared-peptide, parsimony, and protein-rollup choices;
- normalization, imputation, missing-channel, and replicate policy;
- PTM localization ambiguity and protein-abundance correction;
- condition labels, pairing fields, batches, and covariates.

Changing one of these values creates a different analysis, even if inputs and
output filenames stay the same. Preserve the validated configuration and the
typed report together; a command transcript alone does not fully identify the
scientific result.
