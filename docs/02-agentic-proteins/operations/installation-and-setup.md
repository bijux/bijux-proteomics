---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

Install `agentic-proteins` only when an existing application still imports the historical package or invokes the legacy command. New integrations should install and call `bijux-proteomics-runtime` directly.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- the same `0.3.x` release family for `agentic-proteins`, `bijux-proteomics-core`, and `bijux-proteomics-runtime`

The base distribution installs Core and Runtime because compatibility modules forward to those canonical owners. It does not carry independent execution implementations.

## Install the compatibility bridge

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install agentic-proteins
```

Choose an optional dependency only when the legacy application already requires that capability:

```bash
python -m pip install "agentic-proteins[api]"
python -m pip install "agentic-proteins[local-esmfold]"
python -m pip install "agentic-proteins[local-rosettafold]"
python -m pip install "agentic-proteins[nl]"
```

Each extra delegates to the corresponding Runtime extra. Hardware, model assets, service credentials, and provider availability remain Runtime concerns.

## Verify forwarding

Confirm both commands are present:

```bash
agentic-proteins --help
bijux-proteomics-runtime --help
```

Then verify that the historical import resolves to the canonical object:

```python
from agentic_proteins import cli as legacy_cli
from bijux_proteomics_runtime import cli as canonical_cli

assert legacy_cli is canonical_cli
```

That identity check is more meaningful than a successful import alone: it detects accidental package-local implementations that would split behavior between the bridge and Runtime.

## Source checkout

From the repository root, install the package in editable mode when reviewing compatibility changes:

```bash
python -m pip install -e "packages/agentic-proteins[test]"
python -m pytest packages/agentic-proteins/tests
```

Inspect `interfaces`, `orchestration`, `providers`, `state`, and `tools` when a legacy path is in scope. A compatibility change is ready only when the old import still works, resolves to its declared canonical owner, and adds no new execution semantics under `agentic_proteins`.

## Remove the bridge when possible

Migration is complete when the consumer imports `bijux_proteomics_runtime`, invokes `bijux-proteomics-runtime`, and no longer relies on a historical submodule path. Uninstalling `agentic-proteins` should then leave the canonical integration functional.
