---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-07-21
---

# Scope And Non-Goals

`bijux-proteomics-foundation` is the dependency floor for shared contracts. Its
runtime dependency is Pydantic; it does not depend on any product package. This
constraint keeps shared meaning importable without pulling scientific,
execution, evidence, decision, or laboratory policy into every consumer.

## In Scope

- constrained identifiers and identifier-kind helpers;
- strict JSON-backed model behavior;
- canonical JSON, stable values, fingerprints, and hash policies;
- document schema, revision, lineage, and producer metadata;
- shared provenance and typed outcome contracts;
- schema version normalization, compatibility assessment, migration, and
  deprecation;
- tests for deterministic bytes, validation, compatibility, and public API
  budget.

## Explicit Non-Goals

| Concern | Owner |
| --- | --- |
| proteomics formats, algorithms, statistics, benchmark acceptance | Core |
| processes, state machines, providers, retries, replay, services | Runtime |
| citations, claims, evidence graph, biological grounding | Knowledge |
| ranking, confidence, recommendation, refusal policy | Intelligence |
| assay planning, readiness, handoff, outcomes, promotion | Lab |
| compatibility with the historical `agentic_proteins` namespace | Agentic Proteins |
| repository health, release checks, generated governance | Maintainer tooling |

Foundation also does not provide a CLI, HTTP service, database, network client,
plugin system, workflow engine, or domain-specific fixture catalog. Downstream
packages may serialize those concepts using Foundation contracts without
moving their ownership here.

## Growth Rule

A new primitive must have multiple real consumers, one stable cross-package
meaning, no higher-level policy, and a compatibility story proportional to its
expected lifetime. Prefer an explicit downstream contract over a speculative
generic helper.

Reject additions named only by convenience—generic context objects, catch-all
metadata, untyped payload bags, or service locators. They expand dependency
radius without establishing durable semantics.

## Consumer Contract

Consumers may rely on the curated root API and documented specialized modules.
They must not infer scientific validity from schema validity, authenticity from
a content hash, or compatibility from successful deserialization alone.
