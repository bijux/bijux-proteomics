---
title: Python API and CLI Surface
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Python API and CLI surface

Core exposes a curated Python root, domain-specific Python modules, and the
`bijux-proteomics` CLI. It does not own an HTTP application; network execution
belongs to `bijux-proteomics-runtime`.

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

| Export | Purpose |
| --- | --- |
| `DigestPolicy` | declare enzyme, cleavage, missed-cleavage, and peptide filtering behavior |
| `parse_fasta_document` | parse FASTA content into validated sequence records |
| `parse_experimental_design_table` | normalize study and sample design input |
| `build_normalized_run_bundle` | combine normalized run inputs into a portable contract |
| `build_fdr_audit_trail` | retain the decisions behind false-discovery review |

Root imports are lazy and intentionally narrow. Use documented domain modules
for specialized work rather than expecting the package root to mirror the
entire scientific surface.

## Domain APIs

Stable capability families are available beneath:

- `bijux_proteomics.sequences`, `.chemistry`, `.io`, and `.study` for intake
  and normalization;
- `.identification`, `.quantification`, `.dia`, `.ptm`, `.targeted`,
  `.multiplex`, and `.proteoforms` for analysis;
- `.interpretation` and `.review` for governed review artifacts;
- `.benchmarks` and `.workflow` for evidence packages and workflow contracts;
- `.domain` for program, target, assay, lifecycle, and review entities.

Prefer a package's documented facade or `public_api` module when present.
Underscore-prefixed modules and symbols are implementation details even if a
compatibility bridge temporarily imports them.

## CLI design

The CLI uses explicit commands for independently reviewable operations. Use
`--help` at both levels:

```bash
bijux-proteomics --help
bijux-proteomics digest --help
```

Command families include:

| Family | Representative commands |
| --- | --- |
| FASTA and digestion | `fasta-parse`, `fasta-stats`, `fasta-decoy`, `digest`, `theoretical-digest` |
| spectra and chromatography | `spectrum-parse`, `spectrum-annotate`, `mzml-inspect`, `xic-extract`, `xic-score-evidence` |
| identification | `comet-import`, `fragpipe-import`, `maxquant-import`, `sage-import`, `fdr`, `infer-proteins` |
| quantification and DIA | `quantify`, `protein-lfq`, `protein-matrix`, `diann-precursor-matrix`, `diann-run-qc` |
| PTM and targeted | `ptm`, `targeted-panel-builder`, `targeted-transition-selection`, `targeted-result-validator` |
| review and benchmarks | `biological-report`, `validation-evidence-cards`, `public-benchmark-runner`, `build-trust-bundle` |
| workflow | `workflow-plan`, `workflow-validate`, `run` |

## Output contract

Commands distinguish operator messages from scientific artifacts. Portable
results include input lineage, normalized parameters, thresholds, reason codes,
and schema information appropriate to the operation. A non-success must remain
visible as validation failure, processing failure, or scientific refusal; an
empty table is not a generic substitute.

Use [data contracts](data-contracts.md) for object semantics,
[artifact contracts](artifact-contracts.md) for persisted outputs, and
[CLI surface](cli-surface.md) for command-level operational details.
