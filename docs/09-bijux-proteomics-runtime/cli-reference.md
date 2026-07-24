---
title: Runtime CLI Reference
audience: operator
type: reference
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-21
---

# Runtime CLI reference

The `bijux-proteomics-runtime` command manages canonical execution and run
records. Use `--json` for machine-readable command output and `--pretty` for
indented JSON. Unless a governed workflow specifies another location, write
local run products beneath the repository `artifacts/` directory.

## Run or validate a sequence

Provide either an inline sequence or a FASTA file:

```bash
bijux-proteomics-runtime run \
  --sequence MKTIIALSYIFCLVFADYKDDDDK \
  --dry-run \
  --artifacts-dir artifacts/runtime \
  --json
```

`--dry-run` validates and plans without invoking tools. Omit it to execute.
`--rounds` controls the number of rounds; `--execution-mode` accepts `auto`,
`gpu`, or `cpu`.

Real structure providers are opt-in through `--provider`:
`esmfold`, `local_esmfold`, `rosettafold`, `local_rosettafold`, or
`openprotein`. Availability depends on installed extras and environment
capabilities. If no provider is requested, runtime retains its governed default
selection behavior.

## Continue and inspect

```bash
bijux-proteomics-runtime resume CANDIDATE_ID \
  --artifacts-dir artifacts/runtime \
  --json

bijux-proteomics-runtime inspect-candidate CANDIDATE_ID --pretty
```

`resume` re-enters a candidate from governed state and accepts the same rounds,
provider, artifact directory, and execution-mode controls used by `run`.
Inspection is read-only and returns the recorded candidate state.

## Compare and reproduce

```bash
bijux-proteomics-runtime compare RUN_A RUN_B --pretty
bijux-proteomics-runtime reproduce RUN_ID --json
```

Comparison reports differences between completed run records. Reproduction
uses the stored run contract and rejects conditions that cannot support an
honest replay. Neither command asserts scientific equivalence beyond the
recorded comparison fields.

## Import an external result

```bash
bijux-proteomics-runtime import-result \
  --sequence MKTIIALSYIFCLVFADYKDDDDK \
  --source artifacts/external/result.json \
  --engine-name example-engine \
  --engine-version 1.4.0 \
  --artifacts-dir artifacts/runtime \
  --json
```

The engine name, version, source path, and sequence are required. The resulting
record preserves external provenance and remains distinguishable from a native
runtime execution.

## Export a report

```bash
bijux-proteomics-runtime export-report RUN_ID \
  --output artifacts/runtime/report.json \
  --pretty
```

The exported report is a view over the recorded run. Keep the underlying run
bundle when audit, replay, or artifact verification is required.

## Inspect runtime identity

```bash
bijux-proteomics-runtime identity
```

Identity output supports environment and version diagnosis. Record it with
reproduction evidence when provider or dependency differences may matter.

## HTTP API

Start the local application with:

```bash
bijux-proteomics-runtime api serve --host 127.0.0.1 --port 8000
```

Use `--no-docs` to disable interactive OpenAPI documentation and `--reload`
only for local development. The `api` command group also exposes structured
CLI views of `health`, `status`, `history`, `artifacts`, `evidence-bundle`,
`review-packet`, and artifact or evidence lookups.

## Exit and failure behavior

Invalid inputs, missing capabilities, provider failures, corrupt artifacts,
and incompatible replay conditions remain explicit non-success results.
Structured output should be retained with the artifact bundle; do not infer
success from the presence of a partially written directory.

Historical users may invoke the same command group as `agentic-proteins`.
Migrate automation to `bijux-proteomics-runtime`; the compatibility command is
not the canonical name for new integrations.
