---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Review Checklist

Review Core changes for scientific meaning before implementation style. A
result can serialize correctly and still be wrong because orientation, units,
missingness, ambiguity, exclusion, or reference assumptions changed.

## Scientific Contract

- Name the scientific question, accepted input, policy, output, and refusal.
- Record units, coordinate systems, score direction, tolerances, defaults, and
  numerical precision.
- Preserve rejected rows, contaminants, decoys, ambiguous assignments, missing
  observations, and unavailable evidence.
- Separate heuristic, reference-backed, and acceptance-tested behavior.
- State the interpretation ceiling; computation does not establish biological
  or clinical authority.

## Challenge Cases

| Domain | Required pressure |
| --- | --- |
| parsing and import | malformed, partial, duplicated, reordered, unknown fields, field loss |
| sequence and chemistry | terminal cases, ambiguous residues, modification conflicts, mass tolerances |
| identification | reversed orientation, ties, target-decoy edge cases, FDR level, shared peptides |
| quantification | zeros, missingness classes, scaling, batch effects, low replication, censoring |
| spectra and DIA | sparse peaks, tolerance boundaries, library incompleteness, interference |
| PTM | localization ambiguity, site collapse, occupancy overclaim |
| targeted | calibration, carryover, transition interference, failed QC |
| biological interpretation | identifier coverage, background set, circular reference evidence |

## Determinism And Artifacts

- Repeat runs with reordered equivalent input where ordering is not semantic.
- Inspect canonical serialization, stable ordering, hashes, and manifests.
- Retain input identity, method policy, producer version, diagnostics, and
  limitations.
- Compare old artifacts when schemas, defaults, or enumerations move.
- Confirm CLI and Python routes call the same scientific owner and preserve
  failure behavior.

## Boundary Review

Reject provider selection, retry policy, hidden network access, evidence
mutation, recommendation thresholds, and laboratory scheduling in Core. Ensure
new dependencies serve an owned scientific role and do not reverse the package
graph.

## Verification

Run focused domain tests, curated reference and property cases, relevant
benchmark and parity checks, serialization and public-interface checks, then
affected Runtime, Knowledge, Intelligence, or Lab consumers. Record a red
scientific gate as a blocker; do not broaden tolerances or exclusions merely to
restore green status.
