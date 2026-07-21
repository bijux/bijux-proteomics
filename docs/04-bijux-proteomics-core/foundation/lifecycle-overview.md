---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Lifecycle Overview

A core result moves through scientific states, not merely function calls. Each transition adds interpretation while retaining the identity, exclusions, parameters, and provenance needed to review the result.

```mermaid
stateDiagram-v2
    [*] --> Parsed
    Parsed --> Normalized: schema and study checks pass
    Normalized --> Identified: scoring and FDR policy applied
    Identified --> Quantified: roll-up and normalization applied
    Quantified --> Interpreted: context and uncertainty attached
    Interpreted --> Reviewed: evidence product accepted for use
    Parsed --> Rejected: invalid input
    Normalized --> Rejected: design or integrity failure
    Identified --> Inconclusive: insufficient evidence
    Quantified --> Inconclusive: QC or missingness limits
```

## Input lifecycle

Parsers convert external formats into typed records while retaining source-row or source-file lineage. Validation separates malformed input from scientifically unsuitable input. Normalized run bundles bind spectra, design metadata, identifiers, and integrity findings into a comparable analytical starting point.

## Evidence lifecycle

Identification attaches search provenance, scores, target-decoy decisions, peptide evidence, protein grouping, ambiguity, and FDR. Quantification then records matrix construction, normalization, missingness, roll-up, statistics, and QC. Specialized analyses add acquisition, labeling, modification, proteoform, or targeted-assay semantics without erasing those upstream decisions.

Interpretation maps results to biological context and produces review surfaces. It does not promote the output into durable knowledge; consumers decide whether the retained evidence and limitations are fit for that later purpose.

## Re-execution

Stable input contracts, explicit policies, deterministic ordering, atomic output writes, and retained provenance make reruns comparable. A code or policy change that alters scientific output requires a visible contract or result change. Runtime may schedule the computation, but it cannot redefine these scientific transitions.
