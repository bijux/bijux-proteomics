---
title: Runtime Environment Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Runtime Environment Contracts

These contracts record the supported and unsupported environment combinations for each flagship workflow family so runtime claims do not quietly expand beyond the shipped lane.

They matter because `raw_executable` and `rerun ready` are easy to overread. A
family can be executable inside the repository and still fail broader claims
about vendor parity, raw acquisition replay, or outsider-grade consequence
authority. This page names that boundary explicitly.

## How To Read These Contracts

- `required tools` are the minimum execution lane the repository actually owns
- `external dependencies` shows whether the strongest current route still leans
  on imported exports or repository-tracked reports
- `supported combinations` name what the shipped runtime lane can defend today
- `unsupported combinations` are not future ideas; they are present-day claim
  refusals that reviewers should keep visible

## `dda`

- runtime package id: `dda-maxquant-pipeline-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: tracked exported results from `maxquant` 19.0, no live external engine install is required for the shipped rerun lane
- supported combinations: repository-managed python environment plus tracked imported benchmark exports
- unsupported combinations: claiming live external-engine parity from the shipped import lane, claiming raw instrument-side rerun without new tracked inputs and runtime support
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## `dia`

- runtime package id: `dia-diann-pipeline-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked DIA report and comparator exports, library-conditioned review over the shipped benchmark package
- unsupported combinations: claiming chromatogram-native or vendor-parity DIA authority, treating library-conditioned exported reports as a substitute for raw acquisition replay
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## `lfq`

- runtime package id: `lfq-cohort-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## `multiplex`

- runtime package id: `multiplex-tmtpro-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming outsider-auditable multiplex authority from the current internal-support lane
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## `ptm`

- runtime package id: `ptm-localization-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## `targeted`

- runtime package id: `targeted-transition-review-corpus`
- required tools: `python 3.11`, `uv`, `bijux-proteomics-runtime`, `tracked public benchmark package files`
- external dependencies: none beyond tracked repository inputs
- supported combinations: repository-managed python environment plus tracked benchmark package inputs
- unsupported combinations: claiming broader family authority than the shipped benchmark package and downstream consequence surfaces earn
- note: The environment contract names which combinations the shipped runtime lane actually defends and which stronger combinations remain unsupported.

## Why These Contracts Matter Publicly

- they stop runtime documentation from silently expanding beyond what the
  shipped benchmark lane really supports
- they help readers distinguish repository-owned replay strength from broader
  ecosystem parity claims
- they make it clear why some families remain bounded even when their local
  execution story is strong
