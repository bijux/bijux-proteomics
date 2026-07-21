---
title: Extensibility Model
audience: developer
type: architecture
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Extensibility Model

Agentic Proteins extends by preserving migration paths, not by accumulating new
capabilities. A proposed feature should almost always be implemented in the
canonical runtime or the package that owns its scientific meaning, then exposed
here only when an existing legacy import must continue to resolve.

## Admission decision

| Proposed change | Correct owner | Agentic Proteins work |
| --- | --- | --- |
| New CLI command or HTTP endpoint | runtime `api` | Add forwarding only if an existing compatibility contract requires it |
| New run lifecycle, checkpoint, or artifact | runtime `runs` or `state` | Preserve a documented legacy name when necessary |
| New agent, planner, verifier, or tool | runtime `execution` | Provide a narrow alias only for supported old imports |
| New provider or capability policy | runtime `providers` | Forward legacy provider paths; do not duplicate selection logic |
| New scientific model or algorithm | core, intelligence, knowledge, or lab | No local implementation |
| Retirement of a legacy surface | Agentic compatibility governance | Remove only after migration evidence and release communication exist |

## A valid compatibility extension

A new forwarding module is justified only when all of the following hold:

1. A supported legacy import exists in real consumers.
2. The canonical runtime object already owns the behavior.
3. The forwarding path preserves identity or documented observable semantics.
4. Tests exercise legacy and canonical paths together.
5. The compatibility inventory records the surface and its retirement posture.

Prefer explicit imports and `__all__` declarations when the promised surface is
small. Wildcard forwarding is acceptable only where the compatibility contract
intentionally tracks a canonical module and tests detect export drift. Avoid
wrappers that translate exceptions, mutate defaults, copy models, or manage
credentials; each creates behavior that canonical callers do not share.

## Extension smells

- a class has implementation in both Agentic Proteins and runtime;
- a provider is registered locally but absent from the runtime catalog;
- the legacy HTTP route has different validation or error behavior;
- `execution/` and `orchestration/` aliases resolve to different objects;
- a scientific contract is introduced to avoid depending on its owning package;
- a bridge-only option has no migration target; or
- a compatibility module is retained without an observed consumer or removal
  criterion.

The extension is complete when the canonical path is documented first, legacy
and canonical tests agree, dependency direction remains one-way into runtime,
and the bridge exposes no new authority. Compatibility should make migration
boring while steadily reducing the amount of architecture readers must learn.
