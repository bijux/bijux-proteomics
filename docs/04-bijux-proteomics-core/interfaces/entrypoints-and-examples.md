---
title: Entrypoints and Worked Examples
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Entrypoints and worked examples

Use the package root for the compact cross-domain surface, domain packages for
specialized analysis, and `bijux-proteomics` for file-oriented workflows. The
root import is lazy and exposes five stable names: `DigestPolicy`,
`parse_fasta_document`, `parse_experimental_design_table`,
`build_normalized_run_bundle`, and `build_fdr_audit_trail`.

## Inspect FASTA acceptance

```python
from pathlib import Path

from bijux_proteomics import parse_fasta_document
from bijux_proteomics.sequences import FastaParseMode

report = parse_fasta_document(
    Path("proteins.fasta").read_text(encoding="utf-8"),
    mode=FastaParseMode.STRICT,
)

print(f"accepted={len(report.accepted_records)}")
for rejected in report.rejected_records:
    print(rejected.source_identifier, [issue.code for issue in rejected.issues])
```

Do not discard `rejected_records`: they distinguish a clean input from a
partial parse that happened to yield usable records.

The equivalent file-oriented command is:

```bash
bijux-proteomics fasta-parse proteins.fasta --mode strict
```

## Validate a study design

```python
from pathlib import Path

from bijux_proteomics import parse_experimental_design_table

design = parse_experimental_design_table(Path("experimental-design.tsv"))
for entry in design.accepted_entries:
    print(entry.sample_id, entry.condition, entry.replicate, entry.spectra_file)
for row in design.rejected_rows:
    print(row.row_number, [issue.message for issue in row.issues])
```

Parsing confirms the table contract. Check referenced files, biological
balance, randomization, blocking, and acquisition correspondence separately.

## Build a normalized run

```python
from pathlib import Path

from bijux_proteomics import build_normalized_run_bundle

manifest = build_normalized_run_bundle(
    bundle_dir=Path("artifacts/run-a"),
    spectra_path=Path("run-a.mzML"),
    identifications_path=Path("run-a-psms.tsv"),
    design_path=Path("experimental-design.tsv"),
)

print(manifest.document_schema.schema_version)
print(manifest.generated_files)
print(manifest.rejected_spectra, manifest.rejected_identification_rows)
```

Use the returned manifest as the directory inventory and provenance anchor.
Moving or publishing the bundle without its manifest breaks that contract.

## Choose the next surface

- `bijux_proteomics.sequences` owns FASTA, digestion, sequence variation, and
  target-decoy database behavior.
- `bijux_proteomics.io.formats` owns format detection, validation, conversion,
  and normalized run bundles.
- `bijux_proteomics.identification` owns PSM normalization, score orientation,
  FDR, protein inference, and coverage.
- `bijux_proteomics.quantification` owns intensity normalization, missingness,
  differential analysis, and result exports.
- `bijux_proteomics.ptm` owns localized modification evidence and site-level
  analysis.
- `bijux_proteomics.interpretation` owns annotation, enrichment, pathway,
  complex, regulator, and drug-target views.

Start with a normalized input and retain every policy-bearing result. A command
that produces a report is not a substitute for the typed artifact behind it.
