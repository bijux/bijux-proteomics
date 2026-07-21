---
title: Security and Safety
audience: evidence-curator
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Security and Safety

Knowledge artifacts influence scientific decisions, so integrity failures can
be as consequential as unauthorized access. Protect both the confidentiality of
source material and the semantics connecting claims, evidence, context, and
recommendations.

## Control ingestion and reference use

Use explicit reference packs and normalized evidence inputs. Validate their
schemas before they enter a bundle, preserve rejection reasons, and reject
duplicate identifiers rather than overwriting records. A source URI,
bibliographic citation, accession, or accepted fingerprint is metadata; it does
not prove that a source is trustworthy or authorize network access.

The knowledge package does not fetch remote references, manage credentials,
scan attachments, or enforce filesystem and network policy. Applications that
dereference locations must restrict allowed schemes and destinations, apply
timeouts and size limits, authenticate where required, and store secrets
outside knowledge models.

Treat statements, labels, aliases, ontology text, provenance fields, and review
rationale as untrusted data. Escape them in the rendering or query system that
consumes them. Do not turn reference text into commands, templates, or policy
expressions.

## Preserve epistemic safety

- Keep ambiguous protein, ortholog, pathway, and complex membership results
  explicit; do not force them into a unique identity.
- Retain contradictory and adverse evidence through resolution and export.
- Respect source context such as species, tissue, cell line, dose, timepoint,
  assay modality, and endpoint before combining records.
- Downgrade claims when annotation coverage, freshness, triangulation, or trust
  is insufficient.
- Carry caveats, disagreement, holds, and unresolved questions into every
  downstream decision brief.

Fingerprints detect deterministic content changes; they are not digital
signatures, source authentication, or scientific endorsement. Where origin
authenticity matters, the owning repository or application must provide signed
manifests and access-controlled custody.

## Respond to integrity incidents

Freeze affected decision briefs and downstream promotion. Preserve the source
records, normalized bundle, ingestion report, graph validation, conflict
clusters, and fingerprints. Determine whether the incident changed bytes,
identity resolution, graph relationships, context, or trust policy, then find
every brief and export derived from that state.

Publish corrected knowledge as a new attributable bundle with provenance to the
superseded state. Never erase the conflicting record or rewrite a historical
brief: reviewers need to know what evidence was available and why the earlier
recommendation was made.
