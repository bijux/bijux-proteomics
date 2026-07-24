---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

Install `bijux-proteomics-intelligence` when an application needs explainable candidate ranking, evidence posture, scenario judgment, falsification, cautious interpretation, review packets, or learning feedback over already-typed scientific evidence.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- inputs produced under compatible Foundation, Core, and Knowledge contracts

The package installs NumPy, Pydantic, Loguru, and its three canonical upstream packages. It has no provider, service, model-download, or lab-instrument extra.

## Install from PyPI

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install bijux-proteomics-intelligence
```

Verify that the curated owner surface is available:

```python
from bijux_proteomics_intelligence.public_api import (
    list_intelligence_root_api_entries,
)

owners = {
    entry.export_name: entry.owner_module
    for entry in list_intelligence_root_api_entries()
}

assert owners["candidates"].endswith(".candidates")
assert owners["judgment"].endswith(".judgment")
assert owners["posture"].endswith(".posture")
```

Import analytical functions from their owner modules. The package root intentionally exposes owner families and a small set of review surfaces rather than every scoring helper.

## Build a defensible local fixture

A useful fixture contains more than high-scoring candidates. Include:

- candidates with stable identifiers and comparable evidence features;
- missing, stale, contradictory, and ambiguous evidence states;
- an explicit ranking or readiness policy;
- at least one candidate that should be downgraded or refused;
- provenance linking each derived signal to Core or Knowledge inputs;
- expected rationale, uncertainty, and unresolved questions—not only order.

This fixture tests decision behavior. A list that happens to sort correctly cannot prove the package preserved refusal, caveats, or sensitivity to policy.

## Source checkout

From the repository root:

```bash
python -m pip install -e packages/bijux-proteomics-intelligence
python -m pytest packages/bijux-proteomics-intelligence/tests
```

Use the matching family under `tests/candidates`, `tests/judgment`, `tests/posture`, `tests/interpretation`, `tests/reviews`, or `tests/learning` during development. Run cross-family scenarios before release because ranking, readiness, and review artifacts must agree on the same evidence limits.

## Environment boundary

No credentials or remote endpoints are required by the package itself. If a host loads evidence, persists reports, schedules analysis, or exposes an API, those settings belong to Runtime or the application. Keep policy inputs versioned and explicit so two environments do not produce different recommendations under the same unnamed configuration.
