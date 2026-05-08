---
title: Workflow Literature Audits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-05-08
---

# Workflow Literature Audits

`bijux-proteomics-knowledge` now ships one literature audit stack per workflow
family.

The stack is meant to answer four direct questions:

- which citations currently ground this workflow family
- when were those citations last rechecked in the curated registry
- where does the literature still outrun the shipped benchmark or comparator
  proof
- which machine-readable bibliography export should an outsider open first

## Public Surfaces

- `get_workflow_literature_freshness_audit(...)`
- `get_workflow_bibliography_export(...)`
- `get_benchmark_literature_gap_matrix()`
- `get_comparator_literature_gap_matrix()`

## What The Freshness Audit Means

Freshness here is the curated repository audit state.

It records the latest recheck date preserved in the citation and literature
registries, whether a stable DOI or URL still exists in that curated audit, and
whether the current workflow-family summary is already aging past the shipped
literature surface.

It does not pretend that runtime code is doing live citation crawling.

## Machine-Readable Bibliography Exports

Each workflow family exposes one machine-readable bibliography export:

- `workflow_bibliography:dda`
- `workflow_bibliography:dia`
- `workflow_bibliography:lfq`
- `workflow_bibliography:multiplex`
- `workflow_bibliography:ptm`
- `workflow_bibliography:targeted`

Each entry carries title, DOI or stable URL, publication year, relevance tags,
contradiction tags, and freshness state.
