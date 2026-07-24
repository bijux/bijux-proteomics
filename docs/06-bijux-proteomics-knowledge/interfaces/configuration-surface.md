---
title: Knowledge Policy Configuration
audience: mixed
type: reference
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Knowledge policy configuration

Knowledge has no global settings file or implicit annotation database. Each
operation receives its evidence, reference pack, expected biological context,
and policy explicitly. This prevents deployment state from silently changing
the trust or interpretation of a durable evidence bundle.

## Trust policy

`TrustPolicy` names the source and strength weights used to score records. It
also controls penalties for stale records, detected conflicts, duplicate
groups, and preferred maximum age by source type. Defaults distinguish lab
assays, literature, external databases, structure models, and curated notes,
but a project-specific policy should have its own stable `policy_id`.

Trust is not record count. Preserve both the quantity and quality components,
decisive-record count, modality diversity, and integrated score. A large bundle
of duplicated or stale records must not appear stronger merely because it is
large.

## Conflict and resolution policies

`ConflictPolicy` controls which disagreements are detected: shared decision
tags, same-source assay disagreement, opposite quantitative direction, and
effect-size divergence. Detection records a conflict; it does not select a
winner.

`ResolutionPolicy` separately defines:

- the minimum confidence gap for automatic acceptance;
- source-type precedence;
- whether high-severity conflicts force a hold;
- whether biological-context or modality disagreement should be split rather
  than collapsed.

These policies answer different questions and must remain separately
versioned. Weakening detection because resolution is inconvenient hides
evidence; strengthening source precedence does not make two biological
contexts comparable.

## Decision and biological-resolution policies

`DecisionGateProfile` sets minimum trust and triangulation for a direct advance
recommendation in a knowledge brief. Coverage policies for pathways,
complexes, and knowledge entities set their own resolution thresholds. Context
scoring profiles define how species, biological system, and sample type affect
compatibility.

## Configuration invariants

- Pass the reference or annotation pack explicitly and preserve its identity.
- Store policy identifiers with reports; a numeric trust score without its
  policy cannot be reproduced.
- Keep confidence, evidence strength, and source precedence distinct.
- Treat expiry and age policy as review signals, not deletion instructions.
- Never auto-accept high-severity conflicts when the selected resolution policy
  requires a hold.
- A schema-compatible payload may still be scientifically stale, contextually
  incompatible, duplicated, or contradictory.
