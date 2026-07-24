---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-21
---

# Performance and Scaling

Core has several independent scaling regimes. A single “proteomics performance” number is misleading because spectra streaming, peptide-spectrum-match ingestion, protein inference, dense quantitative matrices, enrichment, evidence graphs, and review-packet construction stress different resources.

## Locate the dominant dimension

| Workload | Primary scale dimension | Typical pressure |
| --- | --- | --- |
| mzML or spectrum parsing | spectra, peaks, and input bytes | I/O throughput, XML parsing, and peak memory |
| search-result ingestion | peptide-spectrum matches and columns | parsing, normalization, FDR, and trace export |
| protein inference | peptide–protein edges | graph construction, ambiguity, and grouping policy |
| dense quantification | matrix rows × columns | memory, normalization, rollup, and missingness handling |
| differential analysis | features × contrasts | model fitting and multiple-testing scope |
| PTM processing | peptidoforms, sites, and localization alternatives | combinatorial identity and ambiguity retention |
| evidence or result graphs | nodes, edges, and query volume | graph build, indexing, queries, and packet export |
| review artifacts | candidates, traces, and rendered fields | deterministic ordering, provenance joins, and output size |

## Streaming and materialization

Prefer streaming readers when an operation can consume spectra or rows incrementally. Do not materialize an entire raw file merely for convenience. Operations that require a global ordering, FDR family, protein graph, or cross-sample matrix must state that full-scope requirement because partitioning can change scientific meaning.

Parquet can reduce repeated tabular parsing and improve column-selective access, but conversion is not neutral unless schema, units, nullability, ordering requirements, and provenance remain explicit.

## Governed benchmark surfaces

The performance suite covers parser memory, spectra streaming, million-PSM ingestion contracts, dense quantitative matrices, algorithm families, evidence graphs, indexed result archives, and review packets. Several tests validate benchmark-report semantics from declared observations; they are not claims that every machine achieved the fixture's throughput.

Run the relevant surface from the repository root:

```bash
python -m pytest packages/bijux-proteomics-core/tests/performance
```

For a defensible comparison, record hardware, Python and dependency versions, input identity, record counts, matrix dimensions, timing boundaries, peak memory, output size, and the stage identified as the bottleneck.

## Safe scaling decisions

- Partition only across scientifically independent units such as files, samples, or contrasts whose correction family remains intact.
- Preserve deterministic merge order, identifiers, warnings, and provenance when recombining partitions.
- Keep global FDR, protein inference, normalization, and multiple-testing scopes global when their contracts require it.
- Move orchestration parallelism, queues, retries, and checkpointing to Runtime.
- Optimize an algorithm only with parity fixtures proving unchanged accepted sets, ambiguity, units, and failure behavior.

The correct outcome is not merely faster execution. It is lower cost with the same scientific contract, or an explicitly versioned contract change whose consequences are measured and documented.
