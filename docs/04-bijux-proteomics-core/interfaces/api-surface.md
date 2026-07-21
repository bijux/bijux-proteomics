---
title: Python API and CLI Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Python API and CLI surface

Core offers three deliberate entry routes: a five-name package-root facade,
domain-specific Python modules, and the `bijux-proteomics` CLI. Runtime may
invoke these operations, but core does not expose an HTTP application.

## Curated root API

```python
from bijux_proteomics import (
    DigestPolicy,
    build_fdr_audit_trail,
    build_normalized_run_bundle,
    parse_experimental_design_table,
    parse_fasta_document,
)
```

| Export | Input | Result | Important non-claim |
| --- | --- | --- | --- |
| `parse_fasta_document` | FASTA text and parse policies | accepted records, rejections, duplicates, composition | acceptance does not establish biological correctness |
| `DigestPolicy` | enzyme and filtering assumptions | serializable digestion policy | a valid policy is not evidence that digestion matched the sample |
| `parse_experimental_design_table` | TSV or CSV path | accepted design entries and rejected rows | structural validity does not prove cohort balance or file existence |
| `build_normalized_run_bundle` | spectra plus optional IDs and design | normalized files and a manifest | normalization cannot rescue weak spectra or wrong assignments |
| `build_fdr_audit_trail` | governed PSM records and FDR policy | ranked decisions, q-values, policy, reproducibility hash | target-decoy calculation is not universally appropriate evidence |

The root API has an enforced budget of five public symbols and is loaded lazily.
Specialized capability growth belongs in its owning domain module, not in the
root namespace.

## FASTA acceptance example

```python
from bijux_proteomics import parse_fasta_document

report = parse_fasta_document(
    ">sp|P69905|HBA_HUMAN Hemoglobin subunit alpha\nMVLSPADKTNVKAAWGKVGAHAGEYGAEALERMF\n"
)

assert report.total_records == 1
assert len(report.accepted_records) == 1
assert report.rejected_records == ()
```

Callers consume the report rather than assuming that parsing returned only
sequences. Rejections and duplicate summaries are part of the scientific audit
surface.

## Scientific module families

| Family | Responsibility |
| --- | --- |
| `sequences`, `chemistry` | sequence intake, digestion, modifications, masses, and peptide contracts |
| `io`, `study` | governed formats, normalized run bundles, sample design, contrasts, and validity |
| `identification` | PSM contracts, search adapters, target-decoy calculation, inference, and audit trails |
| `quantification`, `dia` | abundance, matrices, normalization, missingness, DIA evidence, and run QC |
| `ptm`, `targeted`, `multiplex`, `proteoforms` | specialized workflow contracts and reports |
| `interpretation`, `review` | biological summaries, evidence cards, review packets, and limitations |
| `benchmarks`, `workflow` | benchmark evidence and runtime-agnostic workflow plans |
| `domain` | program, target, lifecycle, assay, gate, and review entities |

Use a family facade where it exports the needed name. Use a documented
submodule when the contract is intentionally specialized. Private symbols and
underscore-prefixed modules carry no consumer promise.

## CLI surface

Inspect the installed command tree rather than relying on remembered syntax:

```bash
bijux-proteomics --help
bijux-proteomics fasta-parse --help
bijux-proteomics run --help
```

The command families cover FASTA and digestion, spectra and chromatography,
identification, quantification and DIA, PTM and targeted analysis, biological
review, public benchmarks, workflow planning, validation, and execution.
Commands write scientific artifacts separately from operator messages.

## Failure and refusal behavior

- Invalid command arguments and unreadable inputs produce non-zero CLI exits.
- Parsers preserve row- or record-level rejection when the contract supports
  partial acceptance.
- Unsupported formats and incompatible bundle inputs raise explicit errors.
- Scientific insufficiency is represented as a refusal or report state where
  the operation can explain why it did not produce a claim.
- An empty artifact is never a universal substitute for failure, refusal, or
  zero accepted records.

See [Data contracts](data-contracts.md) for object semantics and
[Artifact contracts](artifact-contracts.md) for portable output requirements.
