---
title: Evidence and Grounding Workflows
audience: mixed
type: how-to
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-07-21
---

# Evidence and grounding workflows

Knowledge work begins with contextual evidence and ends with a reviewable state,
not a single confidence score. Sources, claims, contradictions, resolutions,
and biological mappings remain separately inspectable.

## Ingest evidence

For each observation or source:

1. assign a stable evidence identifier and evidence kind;
2. record source type, locator, origin, extraction method, and curator;
3. capture biological and experimental context;
4. attach quantitative support and proteomics artifact flags;
5. record confidence, strength, observation time, expiry, and derivation;
6. validate the typed record before adding it to a versioned bundle.

```mermaid
flowchart LR
    source["publication · database · run · assay"]
    normalize["contextual normalization"]
    record["EvidenceRecord"]
    bundle["versioned EvidenceBundle"]
    evidence_graph["evidence graph"]
    source --> normalize --> record --> bundle --> evidence_graph
```

Retain imported, observed, inferred, and synthetic origins. Do not convert
missing context into a default that appears observed.

## Build and audit claims

Create claims as references to evidence records, not copies of their prose.
Record supporting and contradicting evidence separately along with assumptions,
resolution assays, polarity, evidence state, confidence, and decision impact.

Validate that evidence identifiers resolve, target context agrees, and decision
lineage reaches the source records. Use evidence-graph integrity checks to find
orphans, duplicate identifiers, invalid edges, and cycles.

## Reconcile conflict

Conflict resolution starts only after disagreement is explicit:

1. classify the contradiction and identify affected claims;
2. compare source quality, context, freshness, quantitative support, and
   independence;
3. apply a declared resolution policy when the basis is sufficient;
4. emit a new resolution record that cites all inputs;
5. place unresolved cases in the escalation queue.

Never edit the losing evidence into agreement. Historical evidence remains
available for replay, calibration, and later reinterpretation.

## Ground biological entities

Use the owned resolution reports for protein IDs, features, pathways, complexes,
kinase-substrate edges, drugs, disease terms, and orthologs. Review every
ambiguous and unresolved row before using the mapped output downstream.

Coverage is a mapping result. It does not establish pathway activity, complex
assembly, kinase causality, therapeutic efficacy, disease mechanism, or
cross-species equivalence. Those conclusions require analytical evidence and a
separate interpretation contract.

## Prepare a decision brief

A knowledge decision brief should include:

- the bounded decision question and target;
- cited supporting and contradicting evidence;
- context and freshness posture;
- unresolved identity or biological mappings;
- claim status, assumptions, and important trust gaps;
- conflict resolutions and outstanding escalation items;
- questions that intelligence or laboratory work must answer next.

Package canonical JSON with reviewer-facing TSV or narrative views. Flat views
must retain identifiers that resolve to the typed record whenever they omit
nested context.

## Evidence handoff contract

Every downstream handoff preserves the evidence state rather than exporting
only a conclusion:

| Handoff field | Required meaning |
| --- | --- |
| bundle identity and schema | exact version of the evidence contract |
| source and evidence identifiers | resolvable path back to origin and extraction |
| context | species, tissue, assay, perturbation, population, and time |
| claim polarity | support, contradiction, qualification, or unresolved relevance |
| derivation | observed, imported, inferred, or synthetic origin |
| freshness | observation time, expiry, and current-use assessment |
| reconciliation | duplicate, superseded, context-specific, or unresolved relationship |
| decision impact | why the record may strengthen, weaken, or block an action |

```mermaid
sequenceDiagram
    participant R as Runtime or assay record
    participant K as Knowledge bundle
    participant I as Intelligence review
    participant L as Lab observation
    R->>K: artifact identity + scientific context
    K->>K: resolve, reconcile, and audit claims
    K->>I: versioned support + contradiction state
    I->>L: advisory question + evidence references
    L-->>K: new observation + QC + deviations
    K->>K: append evidence; preserve prior state
```

Runtime output can be ingested as evidence, but execution success does not
establish claim truth. Intelligence can consume a Knowledge bundle, but its
ranking policy cannot rewrite evidence history. Lab observations return as new
records rather than edits to the recommendation that requested them.

## Maintain evidence over time

Expiry marks a record stale for current decisions without removing it from
history. New observations create new records and can produce a new claim or
resolution state. Governed bundles link evidence to runtime outputs, scientific
summaries, and review artifacts by schema and digest.

A workflow is complete when source context is recoverable, contradictions are
visible, graph integrity passes, ambiguous mappings are retained, freshness is
assessed, and downstream consumers receive a versioned artifact rather than an
unattributed summary.

## Stop conditions

Do not produce a decision-ready bundle when:

- a cited evidence identifier does not resolve;
- source context is missing for a claim whose meaning depends on species,
  tissue, assay, population, or perturbation;
- an inferred or synthetic record is presented as observed;
- an important contradiction is hidden by aggregation;
- entity resolution remains ambiguous but the exported view selects one match;
- an expired record is used without a current-use assessment;
- the evidence graph contains orphaned claims, invalid edges, or cycles;
- a downstream summary cannot be traced to the versioned bundle.

Return an explicit refusal or unresolved state with the failed invariant and
next evidence requirement. An incomplete bundle that looks decisive is more
dangerous than a visible stop.

See [evidence and grounding contracts](../interfaces/data-contracts.md) and
[knowledge artifact contracts](../interfaces/artifact-contracts.md).
