---
title: Library and Service Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Library and service boundaries

`bijux-proteomics-intelligence` installs no executable and exposes no HTTP
application. Its public contract is a set of typed Python decision-support
modules. This is intentional: candidate ranking and recommendation do not own
runtime workspaces, authentication, process control, or automatic progression.

The package root exposes fourteen owner modules lazily:

```python
from bijux_proteomics_intelligence import (
    belief_audit,
    candidates,
    claims,
    contradictions,
    falsifiers,
    governance,
    interpretation,
    judgment,
    learning,
    next_steps,
    posture,
    query,
    refusal,
    reviews,
)
```

Import a concrete class or operation from its owner module. This keeps a
decision path visible in code—for example, ranking from `candidates`, evidence
readiness from `posture`, scenario evaluation from `judgment`, and adaptation
from `learning`.

## Expose intelligence through another surface

| Consumer need | Owning integration |
| --- | --- |
| Run or reproduce computation | `bijux-proteomics-runtime` command or API |
| Render a review packet | Application or reporting layer using a typed intelligence report |
| Persist evidence and contradictions | `bijux-proteomics-knowledge` contracts |
| Schedule a follow-up assay | `bijux-proteomics-lab` after explicit promotion |
| Add authentication, rate limits, or request validation | The service that publishes the endpoint |

When wrapping intelligence in a CLI or service, serialize the complete typed
result. Preserve reason codes, rejected candidates, evidence references,
policy lineage, uncertainty, unresolved questions, and human-review flags.
Returning only the preferred candidate or action turns qualified decision
support into an unjustified command.

`build_intelligence_decision_support_envelope()` marks a recommendation as
`advisory` by default. Only `promote_intelligence_output_to_policy()` creates an
`enforced` envelope, and that operation requires a policy identifier, actor,
and rationale. A transport must not infer promotion from a successful response
or a high score.

For runnable Python examples, see
[Entrypoints and worked examples](entrypoints-and-examples.md).
