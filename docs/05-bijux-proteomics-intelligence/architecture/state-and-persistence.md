---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# State and Persistence

An intelligence record is reproducible only when it preserves the complete basis of the judgment, not merely the selected action.

```mermaid
flowchart LR
    C[Candidate cohort and fingerprints] --> D[Decision record]
    E[Evidence references and posture] --> D
    P[Policy, metrics, weights, thresholds] --> D
    S[Scenario outcomes and uncertainty] --> D
    X[Contradictions, falsifiers, refusals] --> D
    D --> R[Review packet]
    D --> L[Later outcome and learning record]
```

## Durable decision state

- candidate identities, fingerprints, lifecycle states, cohort membership, exclusions, and quality signals;
- evidence references, provenance, freshness, gaps, contradiction state, and readiness result;
- policy identity, metric catalog, weights, thresholds, scenario assumptions, and evaluation time;
- per-scenario action, confidence, hypothesis status, and unresolved questions;
- ranking, ties, robustness, stability, sensitivity, drift, and provenance reports;
- recommendation or refusal, reasons, downgrade chain, gate result, escalation flags, and human-review requirement;
- advisory or enforced mode, including promoter, policy identifier, and rationale;
- review packets, belief audits, challenge results, and later learning records.

## Storage boundary

Candidate stores and artifact records support package workflows, but service persistence remains a runtime concern. Knowledge evidence is referenced rather than copied into an intelligence-owned source of truth. Lab outcomes can be linked for learning without becoming retroactive inputs to an older recommendation.

Decision records should be append-only in meaning: corrections or new evidence create a superseding evaluation. Keeping old policy and evidence snapshots allows reviewers to distinguish a changed world from a changed model.
