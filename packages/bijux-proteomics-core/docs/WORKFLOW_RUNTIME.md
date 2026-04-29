# Workflow Runtime Planning

This guide covers the workflow-runtime planning layer for
`bijux-proteomics-core`. It does not execute search engines or schedulers
directly. It produces stable planning artifacts that downstream runtimes,
operators, and CI surfaces can review, diff, checkpoint, and export.

## Command surface

```bash
bijux-proteomics workflow-plan \
  --proteins proteins.fasta \
  --spectra spectra.mgf \
  --identifications results.tsv \
  --features ms1_features.tsv \
  --design design.tsv \
  --sample-id sample-A \
  --search-adapter generic \
  --dag-out workflow.dag.json \
  --job-out workflow.slurm \
  --checkpoint-out workflow.checkpoint.json \
  --out workflow.bundle.json
```

The command emits one aggregated planning bundle and can also materialize:

- `workflow.dag.json` for DAG-style node and edge inspection
- `workflow.slurm` for scheduler-oriented job export
- `workflow.checkpoint.json` for resumable execution state

## What the runtime bundle contains

The planning bundle is intentionally explicit:

- workflow manifest
- DAG projection
- container step specs
- external search-tool contract
- HPC job descriptor
- cache manifest
- artifact registry
- large-file streaming policy
- parallel execution groups
- workflow checkpoint

## Manifest semantics

The workflow manifest is the stable backbone. It records:

- input files with hashes, sizes, and runtime roles
- execution mode: import existing IDs or run an external search engine
- search adapter choice
- scheduler target
- container image
- ordered workflow steps with dependencies and command previews

The current step model covers:

- input validation
- FASTA digestion
- external search submission when needed
- identification normalization
- FDR
- MS1 quantification when features are present
- QC
- normalized run-bundle materialization

## DAG projection

The DAG projection turns the manifest into runtime-neutral nodes and edges.
This is the handoff surface for downstream orchestration and Bijux DAG
integration work.

Today the DAG plan is still a projected contract, not a live dispatch into
`bijux-core`. That is deliberate: it keeps the proteomics package honest about
what is planned versus what is executed elsewhere.

## Container and scheduler exports

Container step specs make each workflow step explicit about:

- image
- command
- mounts
- work directory
- network policy

The HPC job descriptor then exports those steps as a scheduler-facing script.
Right now the script is an operator-grade planning export for local review and
batch submission prep. It is not yet a full scheduler-integrated runner.

## Cache and artifact lineage

The workflow cache manifest currently covers deterministic reusable surfaces:

- digestion
- search normalization
- spectra parsing
- feature parsing when quant is present

The artifact registry gives every expected workflow output a stable artifact ID,
producer step, output path, and upstream lineage. That makes replay, review,
and downstream runtime integration much less ad hoc.

## Streaming and parallelism

The large-file policy makes eager versus streaming access explicit from file
size and format. The current behavior is conservative:

- `.mzML` is treated as streaming-oriented
- large spectra, identification, and feature files switch to streaming mode
- compact inputs stay eager

Parallel execution groups are derived from declared dependencies, so the output
shows what can run concurrently without relaxing determinism.

## Checkpointing

Checkpoint output records:

- completed step IDs
- ready steps
- blocked steps
- expected artifact IDs per step
- cache manifest hash
- artifact registry hash

That gives operators and downstream runtimes a stable resume contract after
completed digest, normalization, FDR, quant, or QC stages.

## Current boundaries

This layer now provides serious planning and export contracts, but it still does
not provide:

- live scheduler submission
- real container execution
- persistent cache materialization
- automatic checkpoint resume
- true `bijux-core` DAG execution wiring

Those are the next runtime surfaces. The current value is that workflow intent,
lineage, cache expectations, and resumption state are now stable and testable
instead of implicit.
