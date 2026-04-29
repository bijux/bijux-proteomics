# Search Result Adapters

`bijux-proteomics-core` now includes typed search-result adapters for common
engine-style table outputs.

Built-in adapters:

- `comet`
- `msfragger`
- `sage`
- `maxquant-evidence`
- `diann`
- `spectronaut`
- `generic`

## What an adapter owns

Each adapter declares:

- native column expectations
- score orientation
- explicit decoy-label behavior
- protein-reference handling
- whether q-values are expected
- whether config hashing is supported

Use the CLI to inspect the matrix:

```bash
bijux-proteomics search-adapter inspect
bijux-proteomics search-adapter inspect --adapter sage
```

## Normalize one engine table

Normalize a built-in adapter surface:

```bash
bijux-proteomics search-adapter normalize sage results.tsv \
  --adapter-version 0.16.0 \
  --config sage-config.json \
  --jsonl-out normalized.jsonl \
  --provenance-out adapter.provenance.json
```

Normalize a custom table through the generic adapter:

```bash
bijux-proteomics search-adapter normalize generic custom.tsv \
  --mapping-json mapping.json \
  --jsonl-out normalized.jsonl
```

## Provenance

The adapter provenance surface records:

- adapter kind and display name
- adapter version when supplied
- source table path and hash
- config path and hash when supplied
- native column profile
- normalized parse provenance

This keeps engine-specific context attached to the stable PSM output rather
than burying it in ad hoc notes.

## Current boundaries

This surface normalizes engine-like tabular outputs.

It does not yet claim:

- direct execution of the upstream search engines
- parameter-file parsing for every engine
- comparability audits across multiple engine outputs
- full mzIdentML or pepXML adapter coverage
