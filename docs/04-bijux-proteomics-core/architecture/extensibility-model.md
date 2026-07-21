---
title: Extensibility Model
audience: developer
type: architecture
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Core extends by adding scientifically owned contracts and transformations to an
existing domain family. Extension does not mean a generic plugin system: every
new adapter, policy, model, or report must state its proteomics meaning, loss
behavior, validation boundary, and downstream claim limits.

## Choose the owner first

| Proposed capability | Core owns it when | Another owner is stronger when |
| --- | --- | --- |
| File or search-engine adapter | it normalizes proteomics evidence into existing core contracts | it launches or monitors the external process—runtime owns that |
| Scientific model or algorithm | inputs, assumptions, units, and outputs are proteomics-domain meaning | it ranks candidates or recommends action—intelligence owns that |
| Reference annotation | it is measured or derived from the current analysis | it is curated external knowledge—knowledge owns that |
| Assay or QC contract | it defines scientific evidence or acceptance semantics | it schedules staff, materials, instruments, or handoffs—lab owns that |
| Workflow artifact | it assembles reproducible scientific outputs | it manages retries, persistence, telemetry, or providers—runtime owns that |
| Shared primitive | it is specific to proteomics | multiple packages need identical non-domain meaning—foundation owns that |

## Preferred extension patterns

For a new search-engine dialect, add a manifest and dialect contract, normalize
into canonical records, account for every input field, emit rejected rows, and
run conformance against representative fixtures. Extend the existing adapter
registry rather than adding a parallel importer at package root.

For a new analysis, define typed inputs, an explicit policy object, a typed
report, deterministic ordering, and renderers separated from computation.
Attach source lineage, thresholds, warnings, refusals, and limitations. Place it
with the scientific family that owns its invariants, then expose it through the
Python or CLI interface without duplicating the algorithm.

For a new workflow, compose existing domain operations and preserve their
intermediate reports. A workflow may narrow eligibility but must not turn
rejected evidence, unresolved ambiguity, invalid design, or failed QC into an
accepted result.

## Extension proof

An extension is ready when it demonstrates:

1. valid, boundary, and adversarial inputs;
2. deterministic model and table serialization;
3. accepted, rejected, ambiguous, and missing-data accounting;
4. units, score direction, thresholds, and multiple-testing policy;
5. source-to-output provenance and stable identifiers;
6. the claim level the result supports and the conditions that force refusal;
7. interface parity between direct Python use and any CLI exposure; and
8. no dependency on runtime, knowledge, intelligence, or lab internals.

Extension smells include boolean flags that change scientific regimes,
untyped dictionaries crossing domain boundaries, adapters that discard native
fields silently, renderers containing analysis logic, registries without
conformance reports, and convenience exports that bypass an owning subpackage.
Deepen the existing domain model before adding another top-level family.
