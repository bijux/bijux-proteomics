# bijux-proteomics

`bijux-proteomics` is a Python package family for proteomics work that must
remain inspectable after it leaves the process that produced it. It connects
sequence and mass-spectrometry analysis, reproducible execution, evidence
grounding, recommendation review, and laboratory follow-up while keeping each
kind of authority separate.

Use this README to choose an install surface, run a first operation, and locate
repository commands. Use the
[published handbook](https://bijux.io/bijux-proteomics/) when the question is
which evidence supports a scientific, execution, recommendation, or release
claim.

## Product Scope

The repository owns six canonical layers. Foundation defines stable document
semantics. Core owns scientific models and algorithms. Runtime executes and
replays work. Knowledge records why a claim is supportable or contradicted.
Intelligence ranks and challenges possible actions. Lab records whether an
accepted action was feasible and what happened next.

The result is an evidence chain, not one opaque pipeline and not a promise that
every workflow is equally mature. Packages can be installed independently, and
every cross-package handoff has an identifiable owner. The
[product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
traces the full data and decision path.

| If your immediate need is… | Begin with | You receive | This layer cannot authorize |
| --- | --- | --- | --- |
| create stable identifiers, canonical documents, or compatibility decisions | `bijux-proteomics-foundation` | validated document, canonical bytes, digest, schema decision, or typed refusal | source authenticity or scientific equivalence |
| parse, normalize, identify, infer, quantify, or review proteomics data | `bijux-proteomics-core` | typed scientific result, rejections, diagnostics, and active policy | execution history or biological interpretation |
| execute, resume, compare, or replay configured work | `bijux-proteomics-runtime` | run state, environment, checkpoints, artifact ledger, and terminal disposition | scientific acceptance or transfer |
| ground a result against literature, databases, or biological context | `bijux-proteomics-knowledge` | versioned evidence, provenance, support, contradiction, and gaps | candidate ranking or permission to act |
| rank candidates or challenge an action | `bijux-proteomics-intelligence` | policy-bound recommendation, sensitivity, alternatives, or refusal | resource commitment or laboratory execution |
| turn an accepted action into a controlled experiment | `bijux-proteomics-lab` | readiness decision, handoff, observation, and consequence record | retroactive changes to analytical or decision history |
| keep a historical execution caller working while it migrates | `agentic-proteins` | explicit forwarding, parity evidence, canonical destination, and caller disposition | new runtime behavior or proof that every external caller migrated |
| validate repository policy or assemble release evidence | `bijux-proteomics-dev` | named gate result, governed output, candidate record, and publication disposition | scientific truth or permission to ignore a failing owner contract |

## Current Credible Workflow Families

The checked family matrix records the strongest language currently defended by
each complete evidence chain:

| Workflow family | Permitted posture | Execution mode | Limiting fact |
| --- | --- | --- | --- |
| DDA | `review_grade_bounded` | `import_only` | primary and companion lanes review external-engine exports rather than running a repository-owned raw search |
| DIA | `outsider_auditable_bounded` | `raw_executable` over checked reports | library completeness, chromatogram-native replay, and consequence remain bounded |
| LFQ | `outsider_auditable_bounded` | `raw_executable` over checked features | cohort transfer and accuracy beyond repeatability remain bounded |
| multiplex | `internal_support_only` | `raw_executable` over checked features | the companion stress package has a collapsed claim and no outsider consequence closure |
| PTM | `outsider_auditable_bounded` | `raw_executable` over checked localization inputs | localization evidence does not establish occupancy, function, or regulation |
| targeted | `outsider_auditable_bounded` | `raw_executable` over checked targeted QC | calibration transfer, interference, vendor parity, and assay burden remain bounded |

Packet completeness and authority are different. DDA, DIA, LFQ, PTM, and
targeted have full outsider-readable packets, but DDA’s black-box evidence
lowers its requested outsider-auditable language to review-grade. A successful
family packet also does not make the repository release-ready: repository
readiness is conjunctive across black-box execution, benchmark quality,
documentation truth, ownership, artifact hygiene, and consequence evidence.

Read [what one workflow family supports today](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-one-workflow-family-supports-today/)
for the evidence chain and
[release readiness](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/release-readiness-matrix/)
for the revision-specific blockers.

## Forbidden Claims

This repository does not yet claim:

- `release-ready`, `reference-grade`, `elite`, or `product-grade` status;
- universal transfer across cohorts, instruments, search engines, or study
  designs;
- vendor-engine parity from imported result tables;
- biological truth from successful execution alone;
- decision validity without grounding, challenge, and downstream consequence
  evidence.

These are release boundaries, not disclaimers attached after stronger marketing
language. Public wording must remain behind the weakest live benchmark, runtime,
grounding, recommendation, or lab-consequence gate.

| Evidence state | Required public response |
| --- | --- |
| artifact or generated surface is stale | stop and refresh it from its owner before relying on the derived view |
| execution is import-only | describe custody and validation of external results, not native engine execution |
| companion evidence weakens or collapses a claim | narrow or refuse the claim for that workflow family |
| ownership is duplicated or ambiguous | treat the release dossier as blocked until one canonical owner remains |
| consequence evidence is absent | keep the recommendation advisory and state the missing downstream evidence |

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-proteomics?display_name=tag&label=release)](https://github.com/bijux/bijux-proteomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-15%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-proteomics)
[![Published packages](https://img.shields.io/badge/published%20packages-15-2563EB)](https://github.com/bijux/bijux-proteomics/tree/main/packages)

[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

## Reader Paths

Choose the route that matches the decision in front of you. Each route ends at
an inspectable record, not at a narrative summary.

| Reader | Start | Follow until you can inspect |
| --- | --- | --- |
| **Scientist: start with** the [scientist journey](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/scientist-journey/) | the relevant [workflow family](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/) | accepted and rejected inputs, active policy, result, family evidence, and limits |
| **Operator: start with the** [Runtime handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) | the [operator rerun journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/) | request, environment, provider decision, state history, artifact ledger, and comparison |
| **Reviewer: start with** [cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/) | the [Public artifact index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/) | benchmark, run, grounding, recommendation, and consequence records for the same claim |
| **Maintainer: start with** the [safe-change guide](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/bijux-proteomics-dev/maintainer-safe-change/) | the gate named for the changed contract | the owning source, generated evidence, exact check result, and consumer impact |

## Evidence Chain And Authority Stops

```mermaid
flowchart TD
    foundation["Foundation\nidentity · schema · canonical bytes"]
    input["sequence · spectra · search output"] --> core["Core scientific record"]
    core --> scientific{"scientific contract met?"}
    scientific -->|no| narrow["retain evidence; narrow or refuse"]
    scientific -->|yes| runtime["Runtime execution record"]
    runtime --> custody{"execution custody complete?"}
    custody -->|no| narrow
    custody -->|yes| knowledge["Knowledge grounding record"]
    knowledge --> supported{"support burden met?"}
    supported -->|no| narrow
    supported -->|yes| intelligence["Intelligence recommendation record"]
    intelligence --> action{"action stable and authorized?"}
    action -->|no| narrow
    action -->|yes| lab["Lab consequence record"]
    lab -. new observation .-> knowledge
    foundation -. shared contracts .-> core
    foundation -. shared contracts .-> runtime
    foundation -. shared contracts .-> knowledge
    foundation -. shared contracts .-> intelligence
    foundation -. shared contracts .-> lab
```

The solid arrows describe record and evidence movement, not the Python import
graph. Each gate can narrow the claim without invalidating valid records from
an earlier layer. Passing later work never repairs missing scientific
acceptance, execution custody, or grounding.

| Layer | Durable artifact | Stop condition |
| --- | --- | --- |
| Core | scientific report and benchmark acceptance | rejected input, failed acceptance bar, or unsupported transfer |
| Runtime | run bundle, state history, and artifact inventory | refused capability, failed execution, or irreproducible environment |
| Knowledge | evidence bundle and contradiction ledger | unresolved identity, missing context, or insufficient support |
| Intelligence | challenged recommendation record | unstable ranking, unacceptable regret, or required human review |
| Lab | readiness, handoff, and consequence dossier | incomplete controls, unacceptable burden, unsafe execution, or inconclusive outcome |

## Audit one claim end to end

Start with the public sentence you want to defend, not with the package that is
most familiar. A claim such as “this protein group changed under condition B”
crosses several contracts, and each contract can narrow the sentence without
invalidating the records produced earlier in the chain.

| Audit question | Record to open | Evidence that closes the question |
| --- | --- | --- |
| which observations entered the calculation? | Core scientific report | accepted inputs, rejected inputs, normalization policy, workflow family, and benchmark lineage |
| which computation actually produced the artifacts? | Runtime run bundle | resolved request, provider posture, environment, state history, and artifact digests |
| what supports or contradicts the biological interpretation? | Knowledge review bundle | versioned sources, context match, contradiction ledger, and unresolved gaps |
| why did an action outrank its alternatives? | Intelligence recommendation record | candidate universe, policy, sensitivity, falsifiers, downgrade path, and human-review state |
| was the proposed follow-up executable, and what happened? | Lab consequence dossier | readiness decision, controls, deviations, observed outcome, and evidence feedback |

```mermaid
flowchart TD
    claim["public claim"] --> scientific{"scientific record complete?"}
    scientific -->|no| narrow["narrow or refuse the claim"]
    scientific -->|yes| execution{"execution custody complete?"}
    execution -->|no| narrow
    execution -->|yes| grounding{"contextual evidence sufficient?"}
    grounding -->|no| narrow
    grounding -->|yes| decision{"decision stable and reviewable?"}
    decision -->|no| narrow
    decision -->|yes| consequence{"downstream consequence required?"}
    consequence -->|no| bounded["publish a bounded analytical claim"]
    consequence -->|yes| observed{"controlled outcome recorded?"}
    observed -->|no| advisory["keep the action advisory"]
    observed -->|yes| reviewed["publish the reviewed consequence"]
```

The audit stops at the first missing or contradictory record. Later layers may
add context or consequence, but they cannot repair an absent input identity,
an unrecorded provider fallback, or a failed scientific acceptance rule.

## Scientific and Operational Capabilities

The core package covers FASTA parsing, enzymatic digestion, peptide and
fragment chemistry, modification handling, mzML and spectrum models,
identification adapters, false-discovery review, protein inference,
label-free quantification, DIA matrices, PTM analysis, targeted workflows, and
quality-control reports. The surrounding packages add:

- canonical JSON, stable hashes, schema compatibility, and typed outcomes;
- deterministic run configuration, provider selection, checkpoints, resume,
  replay, run comparison, and archive handoff;
- literature and ontology grounding, provenance, contradiction reconciliation,
  and evidence-sufficiency checks;
- candidate filtering, ranking, scenario analysis, counterfactual challenge,
  regret analysis, and refusal;
- assay design, readiness gates, scheduling, lab handoffs, outcome recording,
  and evidence feedback.

Benchmark evidence is family-specific. A strong packet in one family does not
transfer authority to another family, and a public packet does not erase a
weaker runtime lane. See [Workflow families](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-families/)
for family evidence and limitations.

## Package Map

| Distribution | Stable responsibility | Documentation |
| --- | --- | --- |
| `bijux-proteomics-foundation` | identifiers, canonical serialization, schema compatibility, shared outcomes | [Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/) |
| `bijux-proteomics-core` | scientific models, algorithms, adapters, workflow contracts, benchmark assets | [Core](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/) |
| `bijux-proteomics-runtime` | CLI and HTTP execution, providers, checkpoints, replay, run artifacts | [Runtime](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/) |
| `bijux-proteomics-knowledge` | evidence memory, provenance, grounding, contradiction handling | [Knowledge](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/) |
| `bijux-proteomics-intelligence` | ranking, interpretation, challenge, recommendation, refusal | [Intelligence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/) |
| `bijux-proteomics-lab` | assay planning, readiness, scheduling, handoff, outcome feedback | [Lab](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/) |

`agentic-proteins` preserves historical execution imports and commands while
callers move to `bijux-proteomics-runtime`. The `bijux-proteomics`,
`proteomics`, and `proteomics-*` distributions are install/import aliases;
they do not define competing implementations.

## Install Aliases

Install the narrowest canonical distribution that owns the behavior. Alias and
compatibility distributions preserve historical installation surfaces; they do
not create additional product owners.

| Install surface | Resolves to |
| --- | --- |
| `bijux-proteomics` | `bijux-proteomics-core` through the canonical `bijux_proteomics` import root |
| `proteomics` and `proteomics-*` | corresponding canonical `bijux-proteomics-*` distributions |
| `agentic-proteins` | `bijux-proteomics-runtime` plus legacy compatibility submodules |

```bash
python -m pip install bijux-proteomics-core
python -m pip install bijux-proteomics-runtime
```

The packages require Python 3.11 or newer. Runtime and scientific extras are
declared by their owning distributions; consult the relevant package handbook
before enabling provider-backed or external-tool workflows.

## Common Commands

Choose the command by the record you need. The Core CLI operates directly on
scientific inputs and reports. The Runtime CLI owns configured execution,
checkpoints, resume, comparison, and replay.

| Need | Command owner | Result to retain |
| --- | --- | --- |
| inspect or transform scientific inputs | `bijux-proteomics` | typed report, rejected inputs, diagnostics, and policy |
| execute a configured workflow | `bijux-proteomics-runtime run` | run bundle and artifact ledger |
| continue interrupted work | `bijux-proteomics-runtime resume` | continued state history and new terminal disposition |
| compare or reproduce a run | `bijux-proteomics-runtime compare` or `reproduce` | normalized comparison or reproduction record |

```bash
bijux-proteomics --help
bijux-proteomics-runtime --help
```

Treat `bijux-proteomics-runtime` as canonical and `agentic-proteins` as compatibility.
Before changing or removing a legacy entrypoint, run
`make quality-runtime-migration-validation` and inspect the generated module
and compatibility ledgers.

## Run an auditable operation

The smallest useful example parses a FASTA document without discarding rejected
records:

```python
from bijux_proteomics import parse_fasta_document
from bijux_proteomics.sequences import FastaParseMode

report = parse_fasta_document(
    ">sp|P31749|AKT1_HUMAN AKT serine/threonine kinase 1\nMPEPTIDEK\n",
    mode=FastaParseMode.STRICT,
)

for protein in report.accepted_records:
    print(protein.source_identifier, protein.sequence_checksum)
for rejected in report.rejected_records:
    print(rejected.source_identifier, [issue.code for issue in rejected.issues])
```

The report shape illustrates the platform's contract: accepted data, rejected
data, normalization decisions, and diagnostics remain available together.
Larger workflows retain the same evidence discipline through run manifests,
artifact ledgers, grounded claims, recommendation records, and lab outcomes.

For file-oriented use, the equivalent core command is:

```bash
bijux-proteomics fasta-parse proteins.fasta --mode strict
```

Use the [core handbook](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
for scientific workflows and the
[runtime handbook](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
when execution must be checkpointed, resumed, compared, or replayed.

## Evidence and Review Routes

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
  traces data and decisions across package boundaries.
- [Public artifact index](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/public-artifact-index/)
  orders benchmark, runtime, recommendation, and consequence evidence for review.
- [Core package overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/package-overview/)
  maps the scientific surface by domain.
- [Runtime CLI](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/interfaces/cli-surface/)
  documents executable commands and output contracts.
- [Current capability limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)
  states where evidence does not justify a stronger claim.
- [Maintainer handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
  covers local validation, releases, and repository governance.

## Maintainer quick start

- `make help` to list repository automation
- `make ensure-venv` to sync the shared root check environment
- `make test` for the fast unit-focused test matrix
- `make quality` for typing, quality, docs, and MkDocs strict checks
- `make security` for static security and vulnerability gates
- `make quality-artifact-governance` to catch wrong output locations and
  package-root spillover early
- `make quality-architecture-regression` after architecture-facing changes
- `make release-preflight` before cutting a release candidate

These commands are evidence-producing checks, not ceremonial completion
steps. At the current revision, release preflight and broader quality checks
still expose known blockers. Preserve their exact failure output and resolve
the owning contract rather than weakening the gate.

Package-specific commands and checks are documented in their respective
handbooks. Generated reports, logs, and local run products belong under
`artifacts/`.

## Repository operating model

This repository keeps product code, repository automation, and transient local
state separate on purpose:

- runtime code lives in package-owned trees under [`packages/`](packages)
- repository-owned automation lives under [`makes/`](makes),
  [`configs/`](configs), [`apis/`](apis), [`docs/`](docs), and
  [`.github/workflows/`](.github/workflows)
- transient local outputs belong under `artifacts/`; the shared check
  environment is `artifacts/root/check-venv/` and the rendered site is
  `artifacts/root/docs/site/`
- package roots must stay free of local `artifacts/`, `.venv`, caches, logs,
  and generated run products
- package `CHANGELOG.md` files own package release notes, while the root
  [`CHANGELOG.md`](CHANGELOG.md) is only for repository-wide changes
- publishing is tag-driven and fans out into GitHub Release, PyPI, GHCR, and
  docs deployment workflows

This separation keeps scientific ownership visible and makes transient state
safe to remove without confusing it with source or governed evidence.

## Repository Extension Contract

New package surfaces must enter through the same governed mechanisms as the
existing repository:

- add dependency groups and package extras deliberately; supported extras
  include `api`, `local-esmfold`, `local-rosettafold`, `nl`, and `test`;
- use `uv sync --group test` for a test-capable development environment rather
  than creating package-local environments;
- extend the shared quality and security gates, including `interrogate` and `bandit`,
  instead of adding an untracked package-only check;
- update `api-freeze` and `openapi-drift` evidence when public Python or HTTP
  contracts change;
- preserve the distinct `ensure-venv` and `nlenv` environment routes;
- register governed examples and model assets through `manage_examples` and `manage_models`;
- run `make quality-artifact-governance`,
  `make quality-architecture-regression`, and `make release-preflight` before
  treating an extension as repository-complete.

The [maintainer handbook](https://bijux.io/bijux-proteomics/08-bijux-proteomics-maintain/)
maps each extension surface to its owner and gate.

## License

This repository is licensed under the Apache License 2.0. See
[`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
