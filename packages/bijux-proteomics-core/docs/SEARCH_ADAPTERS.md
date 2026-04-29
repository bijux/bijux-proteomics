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

Parse and validate a supported engine configuration:

```bash
bijux-proteomics search-adapter params comet comet.params
bijux-proteomics search-adapter validate-config sage sage-config.json
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

## Compare and verify adapters

Compare two normalized search-result surfaces on a shared score scale:

```bash
bijux-proteomics search-adapter compare \
  sage sage-results.tsv \
  generic sage-results.tsv \
  --right-mapping-json sage-mapping.json
```

Run the built-in conformance checks:

```bash
bijux-proteomics search-adapter conformance sage sage-results.tsv
```

The conformance report now includes:

- rejection-code counts
- q-value and decoy-label contract checks
- protein-reference contract checks
- FDR audit payloads
- calibration plot bins

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

## Score orientation and FDR audit

Engine scores are not assumed to point in the same direction anymore.

- higher-better engines stay ranked by descending score
- lower-better engines such as expectation- or q-like scores are normalized on
  the same best-to-worst rank scale before comparison

The generic FDR workflow can now emit both an audit trail and calibration bins:

```bash
bijux-proteomics fdr results.tsv \
  --score-orientation lower_better \
  --audit-out fdr.audit.json \
  --calibration-out fdr.calibration.json
```

## Current boundaries

This surface normalizes engine-like tabular outputs.

It does not yet claim:

- direct execution of the upstream search engines
- parameter-file parsing for every engine
- full semantic comparison of heterogeneous multi-engine result sets beyond
  normalized overlap, label agreement, and rank-scale deltas
- full mzIdentML or pepXML adapter coverage
