---
title: Security and Safety
audience: operator
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Security and Safety

Agentic Proteins coordinates scientific software; it does not make an execution
environment trustworthy. Operators remain responsible for isolating the
process, controlling credentials, classifying sequence and result data, and
reviewing external-provider terms before a run begins.

## Trust boundaries

The CLI and HTTP package surfaces forward to the runtime, so the same controls
must hold on both paths:

- treat sequences, configuration files, imported results, and human-decision
  files as untrusted input;
- grant the process write access only to its configured workspace and artifact
  root;
- enable external providers explicitly and provide only the credentials they
  require;
- keep credentials outside run configuration, logs, decision rationale, and
  exported bundles;
- require human review where policy or scientific risk demands it; and
- retain the original evidence whenever a run is resumed, imported, or
  reproduced.

Strict model validation rejects unknown fields at major runtime contracts, but
schema validation is not malware scanning or data-loss prevention. Run local
tools and third-party providers in an environment appropriate to their risk.
Network isolation, secret rotation, retention policy, and access control are
deployment responsibilities.

## Artifact safeguards

Runtime ledgers record artifact hashes and retention classes. Import and reuse
paths also enforce configured size guards and reject missing or changed
artifacts. These checks detect accidental or unauthorized modification after an
artifact was recorded; a matching hash proves content equality, not who created
the content or whether its scientific claims are valid.

Never repair a failed integrity report by replacing the recorded hash. Preserve
the affected bundle, restrict access, and create a new run from a trusted input.
Use `import-result` for external output so provider identity, version, and source
lineage remain explicit. Do not place externally generated files into a local
run and present them as native runtime output.

## Scientific control

A coordinator decision is advisory until the configured workflow and review
policy authorize the next action. `partial`, rejected QC, unresolved warnings,
and human-review states must not be promoted to successful evidence by wrapper
logic. The supported resume flow validates a persisted decision and maintains
lineage; editing lifecycle or output JSON bypasses that safeguard.

For incident response, revoke exposed credentials first, preserve the run
directory and structured logs, record the affected run identifiers and
providers, and inspect artifact integrity before reuse. Recovery should produce
a new attributable run rather than rewriting the historical record.
