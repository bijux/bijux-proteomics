---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-04
---

# Local Development

Local work should happen through the publishable packages plus the root
orchestration commands that keep the repository consistent. The goal is not to
make every task happen at the root. The goal is to make cross-package work
visible when it truly becomes cross-package.

## The Usual Path

```mermaid
flowchart LR
    question["a change starts"] --> decision{"one package or many?"}
    decision -->|one package| package["work in the owning package"]
    package --> proof["run package-local tests and update package docs"]
    proof --> commit["commit with durable intent"]
    decision -->|cross-package| root["use root automation and shared checks"]
    root --> review["validate schemas, docs, and package fit together"]
    review --> commit
```

## Working Rules

- make package-local changes in the owning package directory
- use root automation when the change spans packages, schemas, or docs
- keep documentation updates reviewable alongside the code that changes behavior

## Shared Inputs

- `pyproject.toml` for commitizen and workspace metadata
- `tox.ini` for root validation environments
- `Makefile` and `makes/` for common workflows

Start inside the owning package. Come to the root because the work truly spans
packages, not because the root feels more convenient.
