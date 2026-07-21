---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Domain Language

Core terminology follows the scientific chain from observed signal to reviewable analytical evidence.

| Term | Meaning |
| --- | --- |
| **run** | A bounded acquisition and its associated files, instrument context, and sample metadata |
| **experimental design** | The declared mapping among samples, conditions, batches, replicates, pairs, and timepoints |
| **normalized run bundle** | Validated, typed inputs assembled for comparable downstream analysis |
| **spectrum** | An observed mass-to-charge and intensity signal with acquisition identity and metadata |
| **PSM** | A peptide-spectrum match: one candidate interpretation of a spectrum with score and provenance |
| **target-decoy FDR** | An error-rate estimate derived from declared target and decoy competition and threshold policy |
| **peptide evidence** | Identification support aggregated at peptide level without automatically resolving protein ambiguity |
| **protein group** | Proteins represented together because the available peptides do not uniquely distinguish every member |
| **parsimony** | A declared rule for selecting a compact protein explanation of observed peptide evidence |
| **quantification matrix** | Values indexed by biological entity and sample or run, with missingness and provenance retained |
| **normalization** | A declared transformation intended to make values comparable under stated assumptions |
| **roll-up** | Aggregation from a lower evidence level, such as peptide, to a higher entity level, such as protein |
| **PTM localization** | Evidence and uncertainty assigning a modification to one or more candidate residue sites |
| **proteoform** | A molecular form distinguished by sequence variation, processing, or modification state |
| **interpretation** | Contextual analysis of a scientific result; not equivalent to a knowledge claim or recommendation |
| **reviewable evidence product** | Tables, cards, graphs, diagnostics, and reports that retain the basis and limits of a result |

“Passed” must always name the gate that passed. Format validity, QC acceptance, FDR threshold, biological significance, and decision readiness are different judgments. Likewise, “missing,” “filtered,” “rejected,” and “inconclusive” must not be collapsed into a single absent value because they imply different downstream actions.
