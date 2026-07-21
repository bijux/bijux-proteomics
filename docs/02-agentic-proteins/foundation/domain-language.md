---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Domain Language

Compatibility terminology distinguishes a historical route from the behavior it reaches. That distinction prevents migration support from being mistaken for a second runtime architecture.

| Term | Meaning |
| --- | --- |
| **historical surface** | An import path, console command, HTTP path, or optional extra previously exposed by `agentic-proteins` |
| **compatibility bridge** | Code that preserves a historical surface by resolving it to its canonical owner |
| **canonical owner** | The package where behavior, tests, and future development live; for runtime behavior, `bijux-proteomics-runtime` |
| **forwarded symbol** | A public object obtained from the canonical module through a historical import path |
| **object identity** | The requirement that historical and canonical imports resolve to the same class or callable when that is part of compatibility |
| **behavioral parity** | Equivalent inputs, outputs, exceptions, side effects, and artifacts across historical and canonical entrypoints |
| **migration** | A consumer change from a historical surface to the canonical surface |
| **compatibility break** | A historical contract that can no longer be preserved exactly and therefore requires explicit consumer action |

## Names in use

- Distribution: `agentic-proteins`
- Python import root: `agentic_proteins`
- Historical console command: `agentic-proteins`
- Canonical runtime distribution: `bijux-proteomics-runtime`
- Canonical import root: `bijux_proteomics_runtime`

“Agent,” “tool,” “provider,” “run,” and “artifact” describe runtime concepts even when accessed through an `agentic_proteins` path. Documentation should attribute their semantics to runtime and use compatibility language only for the forwarding boundary.

The bridge is not a fork, facade with independent policy, or deprecated placeholder. It is a supported migration surface with a narrow contract: preserve established access without dividing ownership.
