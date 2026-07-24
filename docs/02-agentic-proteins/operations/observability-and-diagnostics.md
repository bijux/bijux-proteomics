---
title: Observability and Diagnostics
audience: operator
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Observability and Diagnostics

Every Agentic Proteins request is observable as a runtime run. The compatibility
surface does not maintain a second execution history: CLI and HTTP requests
produce the same structured run artifacts, lifecycle states, error taxonomy,
and provenance records as the canonical runtime.

## Read a run from the outside in

Start with `run_summary.json`. It answers the operational questions that should
precede log inspection: which run and candidate executed, whether the outcome
was `success`, `partial`, or `failure`, which lifecycle state was reached, and
which failure type, warnings, QC result, and coordinator decision were emitted.

Then correlate the summary with these records:

| Record | Diagnostic value |
| --- | --- |
| `run_output.json` | Typed terminal output, errors, tool status, plan fingerprint, and version metadata |
| `error.json` | Structured failure details for a failed path |
| `lifecycle.json` | State transitions, including a legitimate stop at human review |
| `preflight_report.json` | Workspace, provider, source, and tool-version readiness before execution |
| `timings.json` | Stage duration evidence for latency regressions and stalled providers |
| `telemetry.json` | Runtime event and metric observations tied to the run identifier |
| `logs/run.jsonl` | Component-scoped structured events for detailed chronology |
| artifact ledger and integrity report | Expected files, retention classes, hashes, size guards, and reuse safety |

## Diagnose by boundary

A request that fails validation before provider execution is an input or
configuration problem. A failed preflight is an environment or workspace
readiness problem. A tool failure after a valid plan belongs to the selected
provider boundary. A `human_review` lifecycle with `partial` status is a
controlled hold, not a crashed run. Divergence during `reproduce` is a
reproducibility finding even if both executions finish successfully.

Use the run identifier as the correlation key across HTTP responses, command
output, JSONL logs, telemetry, and artifacts. Preserve machine-readable output
when automating diagnosis; human summaries intentionally omit detail. When
reporting an incident, include the run identifier, command or endpoint,
terminal status, lifecycle state, failure type, plan fingerprint, provider and
tool versions, and the smallest relevant structured artifact. Do not attach
sequences, credentials, or complete provider payloads unless the receiving
system is approved for that data.

An operational repair is verified when the same boundary produces a coherent
summary and output, the lifecycle is explainable, and integrity checks succeed.
Suppressing a warning or deleting an error artifact does not resolve the
underlying condition.
