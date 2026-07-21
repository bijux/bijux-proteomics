---
title: Observability and Diagnostics
audience: practitioner
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Core observability is scientific state expressed through typed reports. These
reports show what entered an analysis, what was rejected, which assumptions
were applied, and why an output is or is not eligible for interpretation. A
process log can explain execution order; it cannot replace this evidence.

## Follow the evidence chain

| Boundary | Primary signals | Questions answered |
| --- | --- | --- |
| Tabular parsing | source row, header and field issue codes, accepted and rejected counts | Was the file structurally understood? |
| Scientific import | normalized identifiers, duplicate findings, row lineage, rejected rows | Which observations became governed records? |
| Program and study design | readiness issues, assay dependencies, contrasts, replicate structure | Is the requested analysis coherent? |
| Identification | target-decoy labels, score direction, thresholds, q-values, ambiguity | Which identifications are supported and under what error control? |
| Quantification | contributors, aggregation policy, sample mapping, missingness ledger | How was each reported abundance obtained? |
| QC | metric values, threshold provenance, reason codes, run and batch decisions | Which evidence blocks promotion? |
| Interpretation | background set, tested hypotheses, correction policy, rejected memberships | Which biological claims are licensed by the inputs? |
| Export | schema, row count, ordering, validation issues, fingerprint | Is the artifact complete and machine-consumable? |

Stable issue codes are the automation interface; messages are the reader
interface. Preserve both. Counts should reconcile across boundaries—for
example, source rows should equal accepted plus rejected rows under the import
contract. A mismatch is itself a diagnostic condition.

## Distinguish failure classes

Malformed rows and unknown columns are ingestion failures. Missing controls,
invalid contrasts, or inconsistent assay dependencies are design failures.
Absent decoys or incompatible score semantics are identification-policy
failures. Excess missingness, contamination, carryover, or drift are QC
findings. A valid computation with an ineligible evidence set is a scientific
refusal, not an infrastructure error.

When recording an incident, include the source fingerprint, normalized
configuration, report type, issue codes, accepted and rejected counts, relevant
thresholds, package version, and output fingerprint. Redact sample identifiers
when necessary, but retain a stable pseudonymous key so evidence can still be
joined across reports.

Diagnostics are complete when a reviewer can trace an output row back to its
source records, identify every transformation and policy decision, and explain
all losses or exclusions without relying on an unstructured console transcript.
