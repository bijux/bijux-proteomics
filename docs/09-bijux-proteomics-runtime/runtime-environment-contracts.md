---
title: Runtime Environment Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-21
---

# Runtime Environment Contracts

A runtime environment contract identifies the tools, tracked inputs, and external dependencies required to reopen one shipped lane. Unsupported combinations are present claim refusals, not an informal roadmap.

```mermaid
flowchart LR
    T["required tools"] --> E["declared environment"]
    I["tracked inputs"] --> E
    D["external dependencies"] --> E
    E --> S["supported combinations"]
    E --> U["unsupported combinations"]
```

## Contract Fields

| field | interpretation |
| --- | --- |
| required tools | minimum repository-owned execution lane |
| external dependencies | systems or imported evidence outside that lane |
| supported combinations | environment combinations defended by retained evidence |
| unsupported combinations | stronger combinations the current release refuses |

## Family Contracts

### `dda`

- runtime package id: `dda-maxquant-pipeline-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: tracked exported results from `maxquant` 19.0, no live external engine install is required for the shipped rerun lane
- supported combinations: repository-managed python environment plus tracked imported benchmark exports
- unsupported combinations: claiming live external-engine parity from the shipped import lane, claiming raw instrument-side rerun without new tracked inputs and runtime support

### `dia`

- runtime package id: `dia-diann-pipeline-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked DIA report and comparator exports, library-conditioned review over the shipped benchmark package
- unsupported combinations: claiming chromatogram-native or vendor-parity DIA authority, treating library-conditioned exported reports as a substitute for raw acquisition replay

### `lfq`

- runtime package id: `lfq-cohort-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn

### `multiplex`

- runtime package id: `multiplex-tmtpro-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming outsider-auditable multiplex authority from the current internal-support lane

### `ptm`

- runtime package id: `ptm-localization-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn

### `targeted`

- runtime package id: `targeted-transition-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn

## Review Rule

An environment claim may expand only when required tools, external
dependencies, replay evidence, and failure behavior expand together. A green
repository execution lane does not erase the unsupported combinations listed
for that family.
