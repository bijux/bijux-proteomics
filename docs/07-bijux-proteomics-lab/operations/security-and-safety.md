---
title: Security and Safety
audience: lab-operator
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Security and Safety

Bijux Proteomics Lab builds reviewable plans, risk assessments, handoffs, and
outcome records. It does not control an instrument, reserve physical materials,
dispatch work to staff, or authorize an experiment. An exported plan becomes
executable only through the laboratory's approved systems and accountable human
processes.

## Maintain the execution boundary

- Accept upstream recommendations only when their evidence references, review
  posture, and unresolved questions are present.
- Require explicit controls, sample and material readiness, instrument and
  staff capacity, risk acceptance, and cleared review gates before handoff.
- Preserve the structured refusal when a proposed assay is not responsible to
  run as written.
- Review LIMS field mappings and all loss notes before import. Successful export
  serialization does not mean the destination retained the plan's meaning.
- Record the accountable approval and local procedure in the execution system;
  do not infer authority from readiness or priority scores.

The package cannot verify physical custody, biosafety level, consent, instrument
maintenance, reagent identity, operator qualification, or local regulatory
requirements. Those controls remain mandatory even when a handoff report is
ready.

## Protect records and identifiers

Treat imported recommendations, free text, sample labels, material identifiers,
LIMS values, and observations as untrusted data. Validate them as typed
contracts and escape them in downstream query, spreadsheet, and rendering
systems. Keep credentials, patient identifiers, and sensitive sample metadata
out of plan rationale and diagnostic exports; use governed identifiers and
least-privilege access to the source system.

Canonical serialization and fingerprints help detect changed artifacts, but
they do not authenticate the approving person, prove custody, or prevent an
authorized user from entering incorrect data. Use the laboratory's signed
audit, access-control, and retention mechanisms for those guarantees.

## Respond safely

If a handoff, plan, export, or observation may have been altered, stop execution
and downstream promotion. Preserve the upstream brief, lab artifact, field
mapping, imported LIMS record, observations, and fingerprints. Reconcile
identifiers and determine whether any physical work already occurred.

Issue corrections as new attributable records. Never rewrite an executed plan,
remove a failed observation, or promote a refused handoff. Durable history is
necessary for scientific learning, incident review, and protection of people,
samples, and equipment.
