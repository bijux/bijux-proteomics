---
title: Security and Safety
audience: decision-reviewer
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Security and Safety

Intelligence outputs are advisory evidence products. They do not authorize a
laboratory action, change a runtime workflow, approve a candidate, or override
an accountable reviewer. The most important safety boundary is preserving that
separation between analytical recommendation and execution authority.

## Govern authority explicitly

- Require a named review process before an `advance`, `scale_up`, or
  next-experiment recommendation becomes operational work.
- Record the decision actor, rationale, evidence references, policy identity,
  and follow-up actions in the owning review or lab system.
- Preserve `hold`, `redesign`, refused claims, unresolved questions, and
  escalation requirements through every export and integration.
- Never let a consumer infer approval from rank, score, confidence, or the
  existence of a recommendation record.
- Re-evaluate stale evidence and material contradictions before promotion.

The package does not control instruments, schedule experiments, manage
credentials, or provide deployment authorization. Integrations that perform
those actions must validate an explicit downstream approval contract rather
than treating intelligence output as executable input.

## Protect decision integrity

Treat imported evidence labels, free text, rationales, and provenance locations
as untrusted data. They may be displayed or compared, but must not become code,
commands, queries, or policy expressions without validation by the consuming
system. Keep secrets and personal identifiers out of evidence references and
review packets; use governed identifiers and access-controlled source systems.

Policy definitions and factor weights are high-impact configuration. Version
them, fingerprint them, review changes, and keep their lineage with each result.
Do not permit an undocumented override to alter ranking or confidence. A stable
fingerprint detects content changes but does not prove that a policy was
approved.

## Resist analytical overreach

Strong claims must retain support thresholds, contradiction checks, falsifiers,
and belief audits. Do not remove adverse evidence, collapse site-specific PTM
uncertainty to protein-level certainty, or present pathway association as a
mechanism. When the contract refuses a claim or recommendation, the safe output
is the refusal plus the required next evidence—not an empty or softened success.

If decision integrity is questioned, freeze downstream promotion, preserve the
complete evidence and review bundle, compare policy and artifact fingerprints,
and identify all consumers of the recommendation. A corrected evaluation must
receive its own attributable context; historical decisions and learning records
remain immutable evidence of what was known at the time.
