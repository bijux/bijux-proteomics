---
title: bijux-proteomics-core
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-07-22
---

# bijux-proteomics-core

`bijux-proteomics-core` is the scientific engine of Bijux Proteomics. It turns
sequence, mass-spectrometry, experimental-design, and search-result inputs into
typed, reviewable scientific artifacts. It also owns the benchmark contracts
used to decide whether a workflow family is ready for public claims.

```bash
python -m pip install bijux-proteomics-core
bijux-proteomics --help
```

## Interpret scientific dispositions

A scientific operation can complete mechanically while rejecting records,
narrowing its conclusion, or refusing the requested claim. Preserve the
disposition alongside the value.

| Disposition | Meaning | Evidence a consumer must retain |
| --- | --- | --- |
| accepted | the result satisfies the declared scientific policy for the tested input and scope | inputs, policy, diagnostics, QC, benchmark context, and limitations |
| accepted with limitations | the result is usable only inside named assumptions, coverage, or transfer bounds | accepted result plus every limiting condition and downstream restriction |
| partially accepted | some records satisfy policy and others do not | accepted and rejected partitions, reason codes, and aggregation consequences |
| rejected record | one input or derived item violates a scientific or data-quality rule | subject identity, rule, observed value, and rejection reason |
| refused workflow | prerequisites or evidence cannot support the requested scientific operation or claim | unmet conditions, requested posture, and valid recovery route |
| failed computation | implementation or environment prevented a governed result | failure identity, diagnostics, partial artifacts, and retry boundary |

`Completed` belongs to execution state, not scientific acceptance. Runtime may
record a completed Core invocation whose scientific report contains rejections,
limitations, or a refusal; both records are correct and neither replaces the
other.

## Scientific pipeline

```mermaid
flowchart LR
    sequence["FASTA\nsequence and contaminants"]
    chemistry["digestion and chemistry\npeptides · modifications · fragments"]
    signal["spectra and chromatography\nMGF · mzML · XIC"]
    identify["identification\nsearch adapters · PSMs · FDR"]
    infer["protein inference\ngroups · parsimony · ambiguity"]
    quantify["quantification\nLFQ · DIA · multiplex"]
    review["review\nPTM · targeted · QC · biology"]
    report["typed scientific report\naccepted · rejected · policy · diagnostics"]
    benchmark["family acceptance\ncorpora · perturbations · limits"]
    sequence --> chemistry
    chemistry --> identify
    signal --> identify
    identify --> infer
    identify --> quantify
    infer --> quantify
    chemistry --> review
    quantify --> review
    sequence --> report
    chemistry --> report
    signal --> report
    identify --> report
    infer --> report
    quantify --> report
    review --> report
    report --> benchmark
```

Each stage exposes its assumptions and result contracts. The package does not
require every analysis to traverse the entire diagram: FASTA operations,
spectrum review, search-result normalization, quantification, and targeted
assay review can be used as independent workflows.

Two paths accompany every supported workflow. The computation path produces a
scientific result; the evidence path records whether that result is credible
under the declared inputs, policies, perturbations, and comparison burden.

```mermaid
flowchart LR
    I["typed input"] --> C["scientific computation"]
    C --> R["result and diagnostics"]
    I --> P["active policy"]
    P --> R
    R --> Q["quality and ambiguity"]
    Q --> B["benchmark acceptance"]
    B --> H["bounded claim"]
```

## A result is more than a value

Core artifacts retain the context needed to challenge a scientific result:

| Review question | Required context |
| --- | --- |
| What was accepted? | parsed records, schema identity, validation policy, and source digest |
| What was rejected? | rejected records, reason codes, thresholds, and strictness mode |
| Which scientific assumptions were active? | digestion, modification, mass-tolerance, FDR, inference, normalization, and workflow policy |
| How stable is the conclusion? | QC metrics, ambiguity, missingness, sensitivity, benchmark acceptance, and known limits |
| Can another system execute it? | typed workflow request, deterministic inputs, expected artifacts, and refusal conditions |

Dropping rejected inputs or active policy makes a concise report easier to
read but weaker to audit. Core keeps these details in machine-readable
artifacts so summaries never become the only surviving record.

## Capability map

| Domain | Implemented surfaces |
| --- | --- |
| sequence and study design | FASTA parsing, filtering, decoys, contaminants, checksums, digestion, sample sheets, feasibility and power estimates |
| chemistry | amino-acid and peptide mass, modifications, isotope envelopes, labels, fragment ions, adducts, open-search unknowns |
| signal and formats | MGF and mzML, spectra, XIC extraction and alignment, chromatography, normalized run bundles, format conversion |
| identification | Comet, DIA-NN, FragPipe, MaxQuant, OpenMS, Sage, and Spectronaut imports; PSM review; target-decoy FDR; calibration; contaminants |
| inference and quantification | peptide evidence, protein grouping and parsimony, LFQ, peptide/protein matrices, missingness, normalization, reproducibility |
| specialized workflows | DIA, PTM, proteoforms, isotope labeling, multiplex, targeted panels and transitions |
| interpretation and review | pathways, contrasts, biological reports, evidence cards, result queries, explanations, QC and failure explanations |
| benchmarks and workflow | public corpora, challenge assets, acceptance bars, workflow planning, validation, trust bundles |

## Interfaces

The curated package root exports a narrow intake path:
`DigestPolicy`, `parse_fasta_document`,
`parse_experimental_design_table`, `build_normalized_run_bundle`, and
`build_fdr_audit_trail`. Domain modules expose the wider Python API.

The `bijux-proteomics` CLI provides focused commands rather than one monolithic
pipeline. Representative routes include:

```bash
bijux-proteomics fasta-stats --help
bijux-proteomics digest --help
bijux-proteomics mzml-inspect --help
bijux-proteomics fdr --help
bijux-proteomics protein-lfq --help
bijux-proteomics diann-run-qc --help
bijux-proteomics ptm --help
bijux-proteomics targeted-panel-builder --help
bijux-proteomics public-benchmark-runner --help
```

Command output is designed for composition: machine-readable artifacts carry
the scientific result and provenance, while concise terminal output supports
operators. HTTP execution belongs to `bijux-proteomics-runtime`.

## Evidence posture

Core ships benchmark assets and acceptance logic, but capability breadth is not
equivalent to uniform validation. DIA, LFQ, PTM, and targeted have
`outsider_auditable_bounded` classifications over checked raw-executable lanes.
DDA is `review_grade_bounded` because its strongest black-box lane begins at
governed search-result import rather than repository-owned raw search
execution. Multiplex remains `internal_support_only`: its checked feature lane
is executable, but transfer is fragile and outsider review and laboratory
consequence are not closed. The
[public benchmark catalog](foundation/flagship-public-benchmark-catalog.md)
links each family to its lineage, comparisons, and limitations.

```mermaid
flowchart LR
    A["algorithm exists"] --> C["contract tests"]
    C --> B["benchmark corpus"]
    B --> H["holdouts and perturbations"]
    H --> T["transfer evidence"]
    T --> P{"public claim burden met?"}
    P -->|yes| E["bounded evidence posture"]
    P -->|no| N["narrow or internal support"]
```

Benchmark evidence is evaluated per workflow family. Success in one family
does not transfer automatically to another instrument, acquisition method,
quantification regime, modification context, or laboratory consequence.

## Anatomy of scientific acceptance

Every accepted result should be reducible to a review record that separates
scientific output from the burden used to accept it.

| Record field | What it preserves | Review question |
| --- | --- | --- |
| workflow family and contract | the exact scientific problem and required outputs | is the acceptance bar relevant to this analysis? |
| input identity | source digests, sample design, references, contaminants, and exclusions | can the analyzed cohort be reconstructed? |
| active policy | tolerances, digestion, modifications, FDR, inference, normalization, and missingness rules | which assumptions could change the conclusion? |
| result and rejection sets | accepted values, rejected records, reason codes, and diagnostics | was inconvenient evidence discarded or retained? |
| acceptance evaluation | metric values, thresholds, holdouts, perturbations, and comparison results | did the record meet its declared burden? |
| evidence posture | internal, review-grade bounded, or outsider-auditable | what may be claimed publicly? |
| known limits | transfer boundaries, unresolved ambiguity, and unsupported contexts | where must the claim stop? |

```mermaid
flowchart TD
    WR["workflow record"] --> VA{"inputs and policy valid?"}
    VA -->|no| RF["typed refusal or failure"]
    VA -->|yes| SC["scientific computation"]
    SC --> AE["acceptance evaluation"]
    AE -->|bar met| BC["bounded claim"]
    AE -->|bar not met| NR["narrow result or no public claim"]
    BC --> KL["known limits remain attached"]
    NR --> KL
```

An acceptance result is not a universal quality label. It applies to the named
family, corpus, policy, and evidence version recorded with the result.

## Read one result against the family ceiling

Core acceptance answers whether one invocation met its declared scientific
contract. Public authority is a second judgment over the complete workflow
family. The weaker judgment controls the sentence that leaves the system.

| Result-level finding | Family posture | Permitted interpretation |
| --- | --- | --- |
| accepted | outsider-auditable bounded | report the accepted result within the family limits and named execution lane |
| accepted | review-grade bounded | retain and review the result; do not describe the family as raw-executable or outsider-auditable |
| accepted | internal support only | use the result for governed internal support; withhold an outsider-facing family claim |
| refused or failed | any posture | preserve the refusal or failure; family evidence cannot turn it into a successful result |

```mermaid
flowchart LR
    invocation["one invocation"] --> acceptance{"scientific contract met?"}
    acceptance -->|no| disposition["refusal · failure · narrowed result"]
    acceptance -->|yes| accepted["accepted result"]
    accepted --> family["family evidence ceiling"]
    family --> public["bounded public statement"]
    family --> internal["review-grade or internal-only use"]
```

Packet readability, execution depth, companion pressure, and consequence
closure belong to the family judgment. They are not properties inferred from
a successful individual run.

## Handoff to Runtime

Core defines scientific meaning and the runtime-agnostic request. Runtime owns
provider selection, execution state, checkpoints, artifacts, and replay.

```mermaid
sequenceDiagram
    participant C as Core contract
    participant R as Runtime
    participant P as Provider
    C->>R: validated workflow request and acceptance policy
    R->>P: resolved execution plan
    P-->>R: outputs, diagnostics, or governed failure
    R-->>C: run bundle with artifact identities
```

A completed run proves that the resolved plan reached a terminal operational
state. Core’s scientific acceptance logic determines whether the outputs meet
the workflow contract.

| Core sends | Runtime adds | Core evaluates on return |
| --- | --- | --- |
| validated request | resolved configuration and provider | artifact schema and scientific completeness |
| input identities and digests | execution state and checkpoints | input/output lineage |
| acceptance policy | logs, diagnostics, and refusal | thresholds, QC, ambiguity, and known limits |
| expected artifact contract | artifact ledger and hashes | family-specific acceptance result |

## Audit A Scientific Statement

“Protein abundance changed” is the end of a scientific argument, not a raw
output. Review the statement backward until every selection, aggregation, and
acceptance decision resolves to a typed record.

| Statement dependency | Record to inspect | A reason to narrow or refuse |
| --- | --- | --- |
| cohort and contrast | experimental design, sample mapping, covariates, exclusions | groups are ambiguous, underpowered, confounded, or changed after analysis |
| peptide evidence | normalized observations, identification confidence, contaminants, missingness | evidence is unsupported, inconsistently mapped, or dominated by loss |
| protein rollup | peptide-to-protein mapping, shared-peptide policy, ambiguity | grouping or parsimony cannot support the named protein-level subject |
| quantitative model | normalization, imputation, weighting, contrast statistic, uncertainty | conclusion depends on an undisclosed or unstable policy choice |
| acceptance | QC, thresholds, perturbations, holdout behavior, benchmark lineage | family-specific burden is unmet or does not transfer to this context |
| public wording | evidence posture and known limits | sentence exceeds the weakest supported dependency |

```mermaid
flowchart LR
    design["study design"] --> observations["accepted peptide observations"]
    observations --> rollup["protein inference and rollup"]
    rollup --> contrast["contrast and uncertainty"]
    contrast --> acceptance["family-specific acceptance"]
    acceptance --> statement["bounded quantitative statement"]
    rejected["rejections · missingness · ambiguity"] -. constrain .-> observations
    policy["normalization · inference · thresholds"] -. constrain .-> contrast
```

The [Workflow Families](../01-bijux-proteomics/foundation/workflow-families.md)
ledger defines the public ceiling, the
[benchmark catalog](foundation/flagship-public-benchmark-catalog.md) supplies
family evidence, [Runtime](../09-bijux-proteomics-runtime/index.md) records the
execution, and [Decision Support](../01-bijux-proteomics/foundation/decision-support.md)
begins only after the scientific statement is accepted.

## Continue By Scientific Question

| Need | Read next | Review is complete when |
| --- | --- | --- |
| map scientific domains to their owners | [package overview](foundation/package-overview.md) | the input, algorithm, result, and refusal all resolve to one scientific owner |
| audit benchmark provenance and redistribution | [benchmark assets](foundation/benchmark-assets.md) and the [asset audit](foundation/benchmark-asset-audit.md) | source, license, selection, digest, acceptance bar, and redistribution boundary resolve |
| inspect family-specific lineage | [DDA](foundation/dda-benchmark-lineage.md), [DIA](foundation/dia-benchmark-lineage.md), [LFQ](foundation/lfq-benchmark-lineage.md), [PTM](foundation/ptm-benchmark-lineage.md), [targeted](foundation/targeted-benchmark-lineage.md), or [multiplex](foundation/multiplex-benchmark-lineage.md) | primary and companion evidence support no stronger than the recorded family posture |
| choose Python, CLI, data, or artifact interfaces | [interfaces](interfaces/index.md) | the route preserves accepted inputs, rejections, policy, diagnostics, and renderable output |
| execute a supported scientific route | [common workflows](operations/common-workflows.md) | the scientific result and Runtime custody record remain distinct and joinable |
| review scientific and implementation limits | [known limitations](quality/known-limitations.md) | every unsupported transfer, ambiguity, and evidence ceiling remains attached to the result |

Core does not own run orchestration, evidence reconciliation, recommendation
policy, or lab scheduling. Those responsibilities belong to runtime,
knowledge, intelligence, and lab respectively.
