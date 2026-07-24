---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Code Navigation

`bijux-proteomics-knowledge` owns the reviewable scientific memory between measured evidence and downstream interpretation. Its source tree separates four concerns that are easy to conflate: curated references, entity resolution, evidence memory, and review artifacts. Begin with the question being answered, then enter the narrowest owner below.

## Public Boundary

The package root is deliberately curated. `public_api.py` records every supported root export, its owning module, classification, and rationale; `governance/charter.py` records the capabilities that justify the package. Read these files before importing an internal model or adding another root symbol.

The root surface exposes stable evidence anchors, schema compatibility, coverage reports, biological resolvers, deterministic renderers, and `KnowledgeDecisionBrief`. It does not make every curation helper public.

## Question-to-owner map

| Question | Owning module family | Preserved distinction |
| --- | --- | --- |
| Can a persisted knowledge document be read safely? | `contracts` | compatible, incompatible, and migration-requiring schemas |
| What scientific sources and fixtures ground a claim? | `references/grounding` | external references, bundled corpora, citations, ontologies, and contextual rules |
| What grounds a workflow or benchmark statement? | `references/workflows` | benchmark manifests, narrative scope, lookups, and briefing caveats |
| Which protein does this identifier denote? | `identity` | exact, unresolved, and ambiguous identity rather than a forced winner |
| What is claimed, and what evidence supports it? | `memory/models` | claims, evidence records, bundles, provenance, and scope |
| Was an input accepted into memory? | `memory/normalization` | accepted, rejected, skipped, and duplicate records with fingerprints and reasons |
| Is the evidence graph internally coherent? | `memory/integrity` | missing references, invalid links, and traceable graph findings |
| How are conflicting records handled? | `memory/reconciliation` | source trust, disagreement, and explicit resolution outcomes |
| Is annotation coverage sufficient? | `coverage` | measured coverage and confidence downgrades for sparse knowledge |
| What biological context applies? | `features`, `kinases`, `disease`, `drugs`, `pathways`, `complexes`, `orthologs` | exact matches, weaker associations, missing members, ambiguity, and coverage |
| What can a downstream reviewer act on? | `reviews` | evidence state, conflicts, critical provenance, readiness, and recommendation |

## Trace a decision brief backward

Start at `reviews/decision_briefs.py` when a conclusion appears surprising. A `KnowledgeDecisionBrief` assembles evidence-state indexes, quality findings, conflict clusters, critical-claim provenance, reference disagreements, readiness, and a bounded recommendation. Follow its claim and evidence identifiers into `memory/models`, inspect reconciliation decisions in `memory/reconciliation`, then trace citations and source context into `references`.

For a biological association, continue into the relevant resolver. A pathway result should expose matched, missing, and unresolved members; a complex result should expose absent subunits; an ortholog result should retain cross-species ambiguity. Coverage is part of the conclusion, not an optional annotation added afterward.

This path distinguishes three very different failures: insufficient measured evidence, insufficient curated context, and a contradiction between otherwise valid sources.
