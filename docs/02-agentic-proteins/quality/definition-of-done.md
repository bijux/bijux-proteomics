---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Definition of Done

Done means the package is easier to trust after the change, not just that the diff merged.

For `agentic-proteins`, done means a legacy surface still forwards correctly, becomes easier to retire, and does not quietly grow into a second runtime.

## Completion Model

```mermaid
flowchart TB
    change["change lands on a legacy CLI, API, or import path"]
    forwarding{"bridge still forwards correctly?"}
    migration{"migration story is clearer afterward?"}
    retirement{"no new permanent bridge obligation added?"}
    done["change is done"]

    change --> forwarding
    forwarding -->|yes| migration
    forwarding -->|no| block1["not done"]
    migration -->|yes| retirement
    migration -->|no| block2["not done"]
    retirement -->|yes| done
    retirement -->|no| block3["not done"]
```

This page should make completion feel stricter than “legacy path still works.” The bridge is only safer after a change when the runtime handoff and retirement pressure are both easier to explain.

## Review Rules

- the edited legacy surface still forwards correctly
- the migration story is clearer than before the change
- no new permanent bridge obligation was added by accident

## First Proof Check

- `packages/agentic-proteins/tests`
- `src/agentic_proteins/interfaces/cli.py` and `interfaces/http/app.py`
- `src/agentic_proteins/execution/` and `src/agentic_proteins/state/`

## Design Pressure

The easy failure is to declare success once a legacy entrypoint still runs, even though the bridge just became broader or harder to retire.
