---
title: Installation and Setup
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-07-21
---

# Installation and Setup

Install `bijux-proteomics-lab` to design and validate experiments, build advisory or executable assay plans, assess readiness, schedule constrained work, produce controlled handoffs, evaluate observations, and reconcile outcomes into the next review cycle.

## Requirements

- Python 3.11 or newer
- an isolated Python environment
- compatible Foundation, Core, and Knowledge packages, installed automatically
- explicit operational inputs for any plan described as executable

Installation does not connect to a LIMS, instrument, inventory service, scheduler, or credential store. Lab produces typed plans and handoff artifacts; external systems execute or persist them.

## Install from PyPI

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install bijux-proteomics-lab
```

Confirm the narrow public entrypoint set:

```python
from bijux_proteomics_lab.public_api import list_lab_root_api_entries

exports = {
    entry.export_name
    for entry in list_lab_root_api_entries()
}

assert exports == {
    "build_advisory_assay_plan",
    "build_executable_assay_plan",
    "plan_experiment_batches",
}
```

An advisory plan describes scientifically motivated follow-up. An executable plan additionally claims that operational requirements are concrete enough to hand off. Keep that distinction visible in application code and interfaces.

## Prepare an operational fixture

A serious local scenario includes:

- assay requirements, dependencies, acceptance rules, and blocking controls;
- sample and material requirements with inventory availability;
- instrument-family capacity and unavailable windows;
- staff availability and review-backlog pressure;
- protocol version, preparation metadata, method metadata, and caveats;
- at least one blocked or refused handoff;
- observed success, caution, failure, and partial-result cases;
- stable identifiers connecting plan, handoff, observation, and feedback.

Planning only abundant, fully controlled work proves little about readiness or refusal.

## Source checkout

From the repository root:

```bash
python -m pip install -e packages/bijux-proteomics-lab "pytest>=8.4.1,<10"
python -m pytest packages/bijux-proteomics-lab/tests
```

Use the owner-aligned test families—`design`, `planning`, `readiness`, `handoffs`, `lifecycle`, `outcomes`, `reconciliation`, and `benchmarks`—during development. A change that crosses the operational loop should exercise both the initial plan and the observed-outcome path.

## Protect real operations

Use synthetic or de-identified fixtures locally. Do not place credentials, patient data, proprietary instrument methods, or uncontrolled exports in source fixtures. Test LIMS mappings against representative schemas and record field loss explicitly before connecting any production integration.
