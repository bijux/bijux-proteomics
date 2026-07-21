---
title: Security and Safety
audience: practitioner
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Security and Safety

The core package processes scientific files and metadata supplied by users and
instruments. Treat every imported table, FASTA record, modification pack,
network edge, annotation set, and configuration document as untrusted until it
passes the applicable parser and domain validation.

## Protect the data boundary

- Use the strict scientific importers and retain their rejected-row ledgers.
  Avoid ad hoc CSV or TSV parsing that silently truncates rows, coerces values,
  or accepts duplicate identifiers.
- Constrain file access and resource use in the calling application. Core
  validates scientific content but does not provide a filesystem sandbox,
  malware scanner, decompression limit, or deployment authorization layer.
- Keep credentials and storage tokens out of study designs, provenance labels,
  exported tables, and exception messages.
- Treat free-text identifiers, annotations, formulas, and provenance URIs as
  data. Do not interpolate them into shell commands, SQL, HTML, or spreadsheet
  formulas without the output system's escaping policy.
- Validate rendered output tables before release. Correct the source or
  transformation when validation fails; do not edit the export in place.

## Preserve scientific safety

Strict parsing is necessary but not sufficient. A syntactically valid dataset
can still lack decoy evidence, replicate support, control coverage, stable
sample mapping, or acceptable missingness. Promotion must follow the typed
readiness and QC decisions, including their threshold provenance and reason
codes.

Do not relabel decoys, reverse score direction, drop ambiguous mappings, impute
missing values, or alter multiple-testing correction merely to obtain a passing
result. Each is a scientific policy decision and must remain explicit in the
configuration and output evidence. Rejected and ambiguous records are part of
the audit trail, not disposable noise.

## Handle sensitive studies

Proteomics tables may encode patient, sample, tissue, or disease information.
The package does not classify or encrypt that data. Use pseudonymous sample
identifiers, least-privilege storage, approved retention, and controlled export
locations. Share the minimum diagnostic extract needed for review and include
fingerprints so it can be correlated with the governed source.

On suspected tampering or accidental disclosure, stop downstream publication,
preserve the source and generated reports, restrict access, and compare recorded
fingerprints and row counts. A matching fingerprint detects content identity,
not authorized origin. Resume only from a validated source under a newly
recorded analysis context.
