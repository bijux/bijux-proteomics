---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-01
---

# Capability Map

The capability map lists the kinds of work `bijux-proteomics-core` is allowed
to do. That list should make the package easier to defend in review, not
broader by default.

The important correction since `v0.3.7` is that the allowed capability set is
much richer than "workflow rules". The package is now allowed to own a broad
scientific center as long as the work still encodes durable scientific law
rather than recommendation policy, evidence truth, or runtime control.

## Allowed Capability Classes

| capability class | examples now visibly owned in core | why that ownership is legitimate |
| --- | --- | --- |
| shared scientific entities | program, target, assay, review, study, sequence, and structure records | downstream packages need one durable scientific object model |
| chemistry and molecular rules | modifications, mass, fragments, isotopes, proteoform and label semantics | these are scientific laws, not runtime or recommendation choices |
| proteomics ingestion and normalization | spectra, mzML, search-adapter, raw-source, and table normalization seams | the product needs typed proteomics inputs before later owners can reason safely |
| evidence-shaping scientific analysis | identification, protein inference, quantification, PTM localization, DIA, targeted, QC | these are still scientific contracts and review surfaces, not recommendation policy |
| benchmark and workflow law | benchmark assets, flagship packages, workflow contracts, lifecycle transitions, review gates | public workflow-family language starts from these roots |

## Reader Test

If a feature answers "what is the durable scientific rule or typed scientific
artifact here?", it is plausibly core. If it answers "should I believe this
claim?", "should I recommend this?", or "can I run this now?", it has probably
left core and moved into knowledge, intelligence, or runtime.

## Disallowed Expansion

- shared schema primitives that belong in foundation
- evidence truth, contradiction ownership, or literature pressure that belong
  in knowledge
- recommendation posture, ranking, or analytical regret that belong in
  intelligence
- operator-facing runtime execution, replay control, and provider handling
- downstream assay-worth or outcome-promotion logic that belong in lab

## What This Map Should Prevent

- hiding biology and chemistry depth under vague "workflow" language
- absorbing recommendation or evidence-truth logic just because core owns the
  strongest scientific machinery
- treating benchmark fixtures as if they were separate from scientific law
- letting runtime convenience redefine the scientific contract

## First Proof Check

- [Package Overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
- [Ownership Boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
- the package source and tests that prove the claimed capability
