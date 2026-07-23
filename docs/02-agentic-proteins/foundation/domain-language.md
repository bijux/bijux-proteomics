---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-22
---

# Domain Language

Compatibility terminology distinguishes a historical route from the behavior it reaches. That distinction prevents migration support from being mistaken for a second runtime architecture.

## Package Vocabulary Anchors

The `agentic-proteins` distribution is implemented under
`packages/agentic-proteins` and exposes the `agentic_proteins` Python import
root. These names identify one compatibility package, not separate products or
runtime owners. References to the hyphenated distribution name describe
packaging and command surfaces; references to the underscored name describe
Python modules and symbols.

| Term | Meaning |
| --- | --- |
| **historical surface** | An import path, console command, HTTP path, or optional extra previously exposed by `agentic-proteins` |
| **compatibility bridge** | Code that preserves a historical surface by resolving it to its canonical owner |
| **canonical owner** | The package where behavior, tests, and future development live; for runtime behavior, `bijux-proteomics-runtime` |
| **forwarded symbol** | A public object obtained from the canonical module through a historical import path |
| **alias contract** | A promise that historical and canonical imports resolve to the same object without translation |
| **adapter contract** | A documented conversion used only when a historical call cannot be represented as a direct alias |
| **object identity** | The requirement that historical and canonical imports resolve to the same class or callable when that is part of compatibility |
| **behavioral parity** | Equivalent declared inputs, outputs, exceptions, side effects, state transitions, and artifacts across historical and canonical entrypoints |
| **caller evidence** | A named consumer, surface used, observed compatibility result, and migration disposition |
| **migration** | A consumer change from a historical surface to the canonical surface |
| **compatibility break** | A historical contract that can no longer be preserved exactly and therefore requires explicit consumer action |
| **retirement-ready** | Every supported caller and retained-state dependency has a canonical replacement and recorded disposition |

## Names in use

- Distribution: `agentic-proteins`
- Python import root: `agentic_proteins`
- Historical console command: `agentic-proteins`
- Canonical runtime distribution: `bijux-proteomics-runtime`
- Canonical import root: `bijux_proteomics_runtime`

“Agent,” “tool,” “provider,” “run,” and “artifact” remain Runtime concepts even
when reached through an `agentic_proteins` path. The historical package owns
access compatibility; Runtime owns their semantics and future behavior.

## Interpret compatibility claims precisely

| Claim | Evidence required | What it does not establish |
| --- | --- | --- |
| “the symbol is forwarded” | historical and canonical object identity | CLI, HTTP, or durable-state parity |
| “the command is compatible” | command discovery, options, defaults, exit status, output, error, state, and artifact comparison | every nested Python path is an alias |
| “the adapter preserves behavior” | declared translation, loss policy, positive and negative fixtures | identity equivalence |
| “the caller migrated” | consumer change and canonical integration evidence | all other callers migrated |
| “the surface can retire” | caller inventory, retained-state proof, release decision, and negative removal test | permission to remove unrelated historical paths |

The bridge is neither a fork nor an independent policy facade. It is a
supported migration surface whose only durable purpose is to preserve named
access while canonical ownership remains singular.
