---
title: Repository Handbook
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-22
---

# Repository handbook

Bijux Proteomics is organized as a scientific product family: six canonical
packages own distinct parts of an auditable workflow, one compatibility
package preserves historical execution surfaces, and one development package
owns repository-wide verification.

The repository is designed so a result can cross process and package boundaries
without losing who produced it, what assumptions were active, why it was
accepted, or which later evidence changed its interpretation.

## Locate a disputed result

Start with the record that made the disputed decision. A downstream package may
render or consume that record, but it does not inherit authority to reinterpret
it silently.

| Dispute | Open first | Decisive evidence | Do not substitute |
| --- | --- | --- | --- |
| two payloads appear to represent the same subject | Foundation identity and compatibility record | canonical bytes, digest, schema decision, and declared migration | matching filenames or display labels |
| a peptide, protein, quantity, or QC result looks wrong | Core scientific report | accepted and rejected inputs, active policy, diagnostics, benchmark burden, and limits | a successful process exit |
| a run completed differently or cannot resume | Runtime run bundle | request, environment, provider, state history, checkpoints, and artifact ledger | a scientific summary |
| a biological claim lacks support or conflicts with another source | Knowledge review bundle | source version, context, relationship, contradiction, freshness, and gap record | rank or recommendation score |
| a candidate was ranked, held, or refused | Intelligence recommendation record | candidate universe, policy, evidence snapshot, sensitivity, alternatives, and reasons | evidence count alone |
| an assay was unready or produced a surprising result | Lab readiness or consequence record | plan, controls, custody, deviations, observations, acceptance, and reconciliation | the original recommendation |
| a repository or release gate disagrees with a package check | maintainer gate and candidate records | exact command, revision, governed inputs, scope, output, and publication disposition | a pass from another revision or surface |

If the decisive record is absent, the conclusion is ungrounded. Follow the
missing identity or handoff upstream; do not infer authority from whichever
package happened to surface the symptom.

## System map

```mermaid
flowchart LR
    F["foundation\nstable meaning"]
    C["core\nscientific computation"]
    R["runtime\nexecution records"]
    K["knowledge\nevidence state"]
    I["intelligence\ndecision posture"]
    L["lab\nexperimental consequence"]
    F --> C --> R --> K --> I --> L
    L -. outcomes .-> K
```

The arrows show evidence movement, not a Python import graph. Foundation
contracts are consumed across the chain; feedback from Lab appends evidence in
Knowledge without mutating the historical recommendation. Governed dependency
directions are listed in
[cross-package ownership](foundation/cross-package-ownership.md).

## Product handoffs

| Handoff | Owner | What crosses the boundary |
| --- | --- | --- |
| foundation contract | `bijux-proteomics-foundation` | identifiers, document schemas, canonical JSON, stable hashes, typed outcomes |
| benchmark asset bundle | `bijux-proteomics-core` | scientific inputs, challenge corpora, acceptance criteria, workflow requests |
| runtime run bundle | `bijux-proteomics-runtime` | run manifest, artifact ledger, checkpoints, replay and comparison records |
| scientific review bundle | `bijux-proteomics-knowledge` | grounded claims, provenance, contradiction ledger, evidence sufficiency |
| recommendation record | `bijux-proteomics-intelligence` | ranking, sensitivity, counterfactuals, stance, refusal explanation |
| lab consequence record | `bijux-proteomics-lab` | assay plan, readiness decision, handoff, observation, feedback |

These artifacts preserve different kinds of truth. Execution success cannot
stand in for scientific validity; evidence support cannot stand in for a
decision policy; and a recommendation cannot stand in for an observed lab
outcome.

## Boundary-crossing contract

Every durable handoff carries four separable identities:

| Identity | Answers | Failure if absent |
| --- | --- | --- |
| subject | which sample, protein, peptide, claim, candidate, assay, or batch? | records cannot be joined safely |
| content | which canonical payload and digest? | equality and replay become ambiguous |
| provenance | which source, producer, policy, and parent records? | a value survives without its derivation |
| disposition | accepted, rejected, refused, failed, superseded, or observed? | absence is mistaken for success |

Cross-package code passes typed records or stable references. Display text,
filenames, and directory position are views of those records, not identity
systems.

## Follow one result across the system

Use identifiers and artifact references to cross a boundary; do not reconstruct
state from filenames or narrative reports.

| Review question | Artifact to inspect | Evidence that must remain visible |
| --- | --- | --- |
| what scientific input was accepted? | core parse or analysis result | policy, accepted records, rejections, source identity |
| what actually ran? | runtime run bundle | resolved configuration, provider, state transitions, checkpoints, artifact digests |
| why is the result supportable? | knowledge review bundle | sources, contexts, supporting and contradicting evidence, freshness |
| why was this action proposed? | intelligence recommendation record | ranking policy, scenarios, falsifiers, downgrade chain, human-review flag |
| what happened after the decision? | lab consequence record | readiness, instructions, observations, QC, deviations, evidence promotion |

```mermaid
sequenceDiagram
    participant C as Core
    participant R as Runtime
    participant K as Knowledge
    participant I as Intelligence
    participant L as Lab
    C->>R: workflow request and scientific contract
    R->>K: run bundle and artifact ledger
    K->>I: grounded claims and contradictions
    I->>L: advisory recommendation or refusal
    L-->>K: observed outcome as new evidence
```

The return arrow creates a new evidence record. It does not retroactively
change the run, claim, or recommendation that preceded the experiment.

## Authority ladder

A claim is only as strong as the narrowest authority it can cite. Start with
scope, follow the record into its owning package, and finish at executable or
externally inspectable evidence.

| Authority | Use it to answer | Do not infer |
| --- | --- | --- |
| [product overview](foundation/product-overview.md) | what the product is designed to cover | that every workflow family has equal evidence |
| [workflow-family ledger](foundation/workflow-families.md) | which families, run modes, and trust levels are declared | that a declared level has passed its current release gate |
| package contract | who owns an input, operation, result, or refusal | that another package may redefine the same concept |
| runtime or scientific record | what happened for one identified invocation | general validity outside its recorded inputs and policy |
| [public artifact index](foundation/public-artifact-index.md) | which evidence is intended for independent inspection | that unpublished or stale evidence supports a public claim |
| [release-readiness matrix](foundation/release-readiness-matrix.md) | which claims are releasable and which remain blocked | that documentation can override a failing gate |

Stop at the first missing identity, unresolved artifact, stale generated
surface, or weaker-than-declared evidence class. A narrative summary never
repairs a broken evidence chain.

## Keep Three Verdicts Separate

The same word—“passed”—can refer to three different review scopes. Every
public statement must name which scope it means.

| Verdict scope | Unit under review | Governing evidence | Valid conclusion |
| --- | --- | --- | --- |
| result disposition | one identified scientific invocation | inputs, policy, accepted and rejected outputs, diagnostics, and Core acceptance | this result met or failed its declared scientific contract |
| workflow-family posture | a primary package, companion pressure package, execution lanes, grounding, challenge, and consequence | family matrix and its named records | this family supports no more than the recorded bounded public language |
| repository release readiness | one source candidate and every required release category | generated readiness matrix and exact gate output | this candidate may publish only when every applicable category passes |

```mermaid
flowchart TD
    result["one scientific result passes"] --> family{"family evidence chain passes?"}
    family -->|no| bounded["retain result; narrow family claim"]
    family -->|yes| posture["bounded family posture"]
    posture --> release{"all repository release categories pass?"}
    release -->|no| withheld["family evidence remains inspectable; release withheld"]
    release -->|yes| eligible["candidate eligible for publication review"]
```

These verdicts are nested constraints, not promotions. A valid result can
belong to an internal-support family. An outsider-auditable family can exist in
a repository whose release candidate is blocked. Neither situation makes the
underlying result false.

## Resolve The Governing Authority

Do not begin a cross-package investigation by searching every source tree.
First identify the kind of authority in dispute, then follow that owner’s
record into implementation and evidence.

| Dispute | Governing route | Resolution evidence |
| --- | --- | --- |
| package or handoff ownership | [Product Architecture](foundation/product-architecture.md) and [Cross-Package Ownership](foundation/cross-package-ownership.md) | one canonical owner, dependency direction, and consumer contract |
| why responsibilities are separate | [Repository Shape Rationale](foundation/repository-shape-rationale.md) | explicit package boundary and the cost of collapsing it |
| strength of a workflow claim | [Workflow Families](foundation/workflow-families.md) | family packet, execution posture, benchmark verdict, and claim ceiling |
| whether evidence is independently inspectable | [Public Artifact Index](foundation/public-artifact-index.md) | resolvable artifact identity, provenance, digest, and reproduction route |
| whether the repository may publish | [Release Readiness Matrix](foundation/release-readiness-matrix.md) | revision-specific gate verdict and closure evidence for every blocker |

```mermaid
flowchart LR
    dispute["disputed statement"] --> kind{"which authority?"}
    kind -->|meaning or identity| foundation["Foundation contract"]
    kind -->|scientific result| core["Core evidence"]
    kind -->|execution history| runtime["Runtime bundle"]
    kind -->|support or contradiction| knowledge["Knowledge review"]
    kind -->|ranking or refusal| intelligence["Intelligence decision"]
    kind -->|feasibility or outcome| lab["Lab consequence"]
    foundation --> proof["implementation · tests · retained artifact"]
    core --> proof
    runtime --> proof
    knowledge --> proof
    intelligence --> proof
    lab --> proof
```

## Continue By Objective

Choose a route by the question you need to answer:

| If you are trying to… | Begin here | Continue with |
| --- | --- | --- |
| establish product scope | [Product Overview](foundation/product-overview.md) | [Workflow Families](foundation/workflow-families.md) and the release-readiness matrix |
| understand package ownership | [Product Architecture](foundation/product-architecture.md) | [Cross-Package Ownership](foundation/cross-package-ownership.md) and the package handbook |
| assess scientific coverage | [Workflow Families](foundation/workflow-families.md) | the relevant Core workflow handbook, benchmark evidence, and [current capability limits](foundation/current-capability-limits.md) |
| follow a scientific analysis | [Scientist Journey](foundation/scientist-journey.md) | Core results, Runtime execution evidence, and Knowledge review records |
| reproduce a result | [public artifact index](foundation/public-artifact-index.md) | the [Operator Rerun Journey](../09-bijux-proteomics-runtime/operator-rerun-journey.md) and Runtime comparison records |
| judge a biological claim | [Knowledge grounding and contradiction guidance](../06-bijux-proteomics-knowledge/index.md) | [Intelligence sensitivity and refusal guidance](../05-bijux-proteomics-intelligence/index.md) |
| take a result into the laboratory | [Intelligence recommendation records](../05-bijux-proteomics-intelligence/index.md) | [Lab readiness, handoff, QC, and outcome capture](../07-bijux-proteomics-lab/index.md) |
| contribute or release a change | [local development](operations/local-development.md) | [testing and validation](operations/testing-and-validation.md), [Maintainer Safe Change](../08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change.md), and [Maintenance](../08-bijux-proteomics-maintain/index.md) |

## Canonical packages

- [Foundation](../03-bijux-proteomics-foundation/index.md)
- [Core](../04-bijux-proteomics-core/index.md)
- [Runtime](../09-bijux-proteomics-runtime/index.md)
- [Knowledge](../06-bijux-proteomics-knowledge/index.md)
- [Intelligence](../05-bijux-proteomics-intelligence/index.md)
- [Lab](../07-bijux-proteomics-lab/index.md)

Use [agentic-proteins](../02-agentic-proteins/index.md) only for compatibility
with historical runtime imports, commands, or API routes. New execution work
belongs in the runtime package. Repository verification and release operations
live in the [maintainer handbook](../08-bijux-proteomics-maintain/index.md).

## Trust boundaries

The platform intentionally does not claim universal proteomics coverage or
automatic biological truth. Confidence is bounded by the workflow-family
benchmark, recorded execution conditions, source quality, contradiction state,
decision sensitivity, and feasibility of downstream validation. Each package
can refuse work when its part of that chain is under-specified.

| A visible artifact proves… | It does not prove… |
| --- | --- |
| canonical payload equality | source authenticity or biological equivalence |
| completed Runtime execution | scientific acceptance or transfer |
| benchmark acceptance | validity outside the tested family and conditions |
| grounded support | absence of contradiction or authority to act |
| stable recommendation under tested scenarios | feasibility or laboratory value |
| completed assay | generality beyond the recorded controls and batch |

## Review protocol

A cross-package conclusion is acceptable only when each boundary has an
identified record and its refusal route remains visible.

| Review boundary | Accept only when | Refuse or narrow when |
| --- | --- | --- |
| scientific result | accepted and rejected inputs, active policy, diagnostics, and family acceptance remain attached | exclusions, assumptions, ambiguity, or workflow family cannot be reconstructed |
| execution custody | configuration, selected provider, state transitions, artifacts, and terminal disposition resolve to one run | completion is asserted from terminal output without the run bundle |
| evidence grounding | every support or contradiction reference resolves to a versioned source and compatible context | prose summarizes support that cannot be reopened or conflict has been omitted |
| recommendation | candidate universe, policy, sensitivity, alternatives, and human-review state are explicit | a score is presented as an authorized action or instability is hidden |
| laboratory consequence | readiness, controls, handoff, deviations, observation, and disposition share custody | an advisory plan is presented as executed or an observation as biological truth |
| history | later reviews and outcomes append records linked to their predecessors | an earlier result, evidence bundle, or recommendation must be overwritten to explain the current state |

The first unresolved row controls the strongest defensible conclusion. A
complete record later in the chain cannot compensate for an absent owner or
failed contract earlier in it.
