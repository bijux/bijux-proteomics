---
title: Compatibility Commitments
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Compatibility commitments

Core compatibility covers more than import paths. Scientific callers depend on
field meaning, units, validation boundaries, deterministic results, and the
shape of review evidence. Preserving a function signature while changing one
of those properties is still a compatibility change.

## Stable surfaces

| Surface | Commitment |
| --- | --- |
| curated `bijux_proteomics` root exports | remain deliberately small and load lazily |
| documented owner-module APIs | retain typed inputs, outputs, and scientific meaning across compatible releases |
| `bijux-proteomics` CLI | preserve command names, declared options, exit behavior, and structured output contracts |
| persisted schemas | retain readable versions or provide an explicit migration decision |
| `proteomics-core` alias | forward canonical exports without independent scientific behavior |

The root currently exposes `DigestPolicy`, `parse_fasta_document`,
`parse_experimental_design_table`, `build_normalized_run_bundle`, and
`build_fdr_audit_trail`. Deeper capabilities are imported from their owning
modules so the root does not become an unbounded convenience namespace.

## Scientific compatibility

The following changes require explicit impact review even when Python accepts
the same call:

- a unit, normalization, tolerance, or default changes;
- an accepted value becomes rejected, coerced, or silently omitted;
- ambiguity, contamination, missingness, or uncertainty is collapsed;
- an algorithm changes ordering, grouping, scoring, or threshold behavior;
- a report stops carrying assumptions, exclusions, or provenance needed to
  interpret the result.

Floating-point stability means results remain within a declared scientific
tolerance, not that every platform must emit identical incidental formatting.
Identifiers, categorical states, canonical serialization, and stable hashes
may require exact equality where their contracts say so.

## Add, narrow, or break

An additive field must have a defensible default or remain optional to old
readers. Tightened validation is a narrowing change. Renaming a command,
changing output columns, reinterpreting a status, or removing an owner-module
symbol is breaking unless a supported compatibility route preserves the old
contract.

Compatibility aliases do not make two owners. New scientific behavior lands in
`bijux-proteomics-core`; `proteomics-core` forwards it only after the canonical
surface and tests exist.

## Verification

```bash
make test PACKAGE=bijux-proteomics-core
make api PACKAGE=bijux-proteomics-core
make build PACKAGE=bijux-proteomics-core
make test PACKAGE=proteomics-core
```

Release evidence pairs API and import checks with scientific reference cases,
serialized artifact fixtures, and CLI output tests where those surfaces are
affected. Changelog entries name the changed contract and observable impact;
“internal refactor” is accurate only when these proofs show no public semantic
change.
