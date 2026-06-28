# bijux-proteomics-core

<!-- bijux-proteomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-core/)
[![Typing: typed](https://img.shields.io/badge/typing-typed%20(PEP%20561)-0A7BBB)](https://pypi.org/project/bijux-proteomics-core/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![CI Status](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml?query=branch%3Amain)
[![GitHub Repository](https://img.shields.io/badge/github-bijux%2Fbijux--proteomics-181717?logo=github)](https://github.com/bijux/bijux-proteomics)

[![bijux-proteomics-core](https://img.shields.io/pypi/v/bijux-proteomics-core?label=core&logo=pypi)](https://pypi.org/project/bijux-proteomics-core/)
[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins?label=agentic--proteins&logo=pypi)](https://pypi.org/project/agentic-proteins/)
[![bijux-proteomics-foundation](https://img.shields.io/pypi/v/bijux-proteomics-foundation?label=foundation&logo=pypi)](https://pypi.org/project/bijux-proteomics-foundation/)
[![bijux-proteomics-runtime](https://img.shields.io/pypi/v/bijux-proteomics-runtime?label=runtime&logo=pypi)](https://pypi.org/project/bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence](https://img.shields.io/pypi/v/bijux-proteomics-intelligence?label=intelligence&logo=pypi)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge](https://img.shields.io/pypi/v/bijux-proteomics-knowledge?label=knowledge&logo=pypi)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![bijux-proteomics-lab](https://img.shields.io/pypi/v/bijux-proteomics-lab?label=lab&logo=pypi)](https://pypi.org/project/bijux-proteomics-lab/)

[![bijux-proteomics-core](https://img.shields.io/badge/core-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-core)
[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fagentic-proteins)
[![bijux-proteomics-foundation](https://img.shields.io/badge/foundation-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-foundation)
[![bijux-proteomics-runtime](https://img.shields.io/badge/runtime-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-runtime)
[![bijux-proteomics-intelligence](https://img.shields.io/badge/intelligence-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-intelligence)
[![bijux-proteomics-knowledge](https://img.shields.io/badge/knowledge-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-knowledge)
[![bijux-proteomics-lab](https://img.shields.io/badge/lab-ghcr-181717?logo=github)](https://github.com/bijux/bijux-proteomics/pkgs/container/bijux-proteomics%2Fbijux-proteomics-lab)

[![bijux-proteomics-core docs](https://img.shields.io/badge/docs-core-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/02-agentic-proteins/)
[![bijux-proteomics-foundation docs](https://img.shields.io/badge/docs-foundation-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/)
[![bijux-proteomics-runtime docs](https://img.shields.io/badge/docs-runtime-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/)
[![bijux-proteomics-intelligence docs](https://img.shields.io/badge/docs-intelligence-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/)
[![bijux-proteomics-knowledge docs](https://img.shields.io/badge/docs-knowledge-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/)
[![bijux-proteomics-lab docs](https://img.shields.io/badge/docs-lab-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/)
<!-- bijux-proteomics-badges:generated:end -->

`bijux-proteomics-core` is the scientific heart of the suite and the semantic
owner for durable proteomics meaning in this repository. It owns the domain
models, evidence normalization, uncertainty-aware review artifacts, and
workflow contracts that the surrounding packages consume.

Within the suite, core owns benchmark assets, durable scientific contracts, and
workflow requests.

Use this package when the change defines scientific meaning that should remain
true before runtime execution, knowledge curation, intelligence judgment, or
lab operations are layered on top.

Core also owns workflow blueprints and execution requests, but only as
runtime-agnostic scientific contracts. It does not take over provider binding,
run orchestration, ranking policy, reference curation, or lab readiness.

## Why teams pick this package

- explicit scientific contracts for sequence, chemistry, identification, quantification, PTM, DIA, study, and review surfaces
- deterministic evidence normalization with honest loss and refusal reporting
- workflow contracts that stay runtime-agnostic while preserving scientific meaning
- reviewable artifacts that downstream packages can consume without redefining core domain truth

## Typical use cases

- normalize proteomics evidence into durable core contracts before higher-layer judgment begins
- model program, target, assay, review, and workflow state with explicit scientific semantics
- inspect unsupported or lossy scientific inputs without hiding uncertainty
- build reviewable scientific artifacts that runtime, knowledge, intelligence, and lab can consume

## Installation

```bash
pip install bijux-proteomics-core
```

## Quick start

The core CLI is a domain toolkit for scientific parsing, normalization, and
report preparation. It is not the flagship workflow runner.

```bash
bijux-proteomics --help
```

For end-to-end workflow execution and reviewable runs, start from
`bijux-proteomics-runtime` instead.

For one minimal non-developer CLI path over the shipped local dataset, start
with the [Shipped demo CLI tutorial](docs/SHIPPED-DEMO-CLI.md).

Import-driven usage starts from the core domain package:

```python
import bijux_proteomics.domain.program_spec as program_spec
import bijux_proteomics.domain.validation as validation
```

For reader-facing examples that stay inside the scientific package boundary:

```python
from bijux_proteomics.interfaces import (
    build_glycopeptide_refusal_example,
    build_loss_aware_search_normalization_example,
    build_sequence_digest_example,
)

digest_example = build_sequence_digest_example()
refusal_example = build_glycopeptide_refusal_example()
loss_example = build_loss_aware_search_normalization_example()
```

Those examples are built from real core functions and show:

- a digest walkthrough that needs no runtime context
- an explicit refusal when glycopeptide evidence is incomplete
- a loss-aware normalization report for external search-engine fields

The interface layer is split on purpose:

- `bijux_proteomics.interfaces` is the curated reader-facing example surface
- `bijux_proteomics.interfaces.python_api` exposes programmatic command runners
- `bijux_proteomics.interfaces.cli` owns the interactive CLI entrypoint
- `bijux_proteomics.interfaces.support` is a compatibility registry of support
  submodules; internal package code should import owner modules such as
  `foundation`, `identification`, `interpretation`, `io_and_dia`,
  `multiplex_targeted`, `ptm_quantification`, `review_sequences_study`, and
  `workflow` directly

Sequence intake and FASTA operations now live in the same package surface:

```bash
bijux-proteomics fasta-parse proteins.fasta --mode strict
bijux-proteomics fasta-stats proteins.fasta --mode permissive
bijux-proteomics fasta-dedup proteins.fasta --mode permissive --out-fasta proteins.dedup.fasta
bijux-proteomics fasta-filter proteins.fasta --organism "Homo sapiens" --exclude-contaminants --out-fasta human.fasta
bijux-proteomics fasta-decoy proteins.fasta --decoy-mode reverse --out-fasta target-decoy.fasta
bijux-proteomics target-decoy-validate target-decoy.fasta
```

For deterministic decoy workflows, the CLI can also emit a reproducibility
manifest:

```bash
bijux-proteomics fasta-decoy proteins.fasta \
  --decoy-mode shuffle \
  --seed 11 \
  --out-fasta target-decoy.fasta \
  --manifest-out target-decoy.manifest.json
```

Import-driven sequence usage is also public and stable:

```python
from bijux_proteomics.sequences import (
    FastaParseMode,
    build_fasta_stats,
    parse_fasta_document,
    validate_target_decoy_database,
)
```

Peptide generation and indexing surfaces are available from the same package:

```python
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    build_digest_duplicate_accounting,
    build_digest_policy,
    build_peptide_protein_index,
    classify_peptide_uniqueness,
    compute_digest_policy_hash,
    digest_sequence,
    get_protease_rule,
)

peptides = digest_sequence(
    "MKWVTFISLLFLFSSAYSRGVFR",
    protease=get_protease_rule("trypsin"),
    missed_cleavages=1,
    mode=PeptideDigestionMode.FULL,
)
policy = build_digest_policy(
    protease="trypsin",
    digestion_mode=PeptideDigestionMode.FULL,
    missed_cleavages=1,
    min_length=7,
    max_length=30,
    min_mass=None,
    max_mass=None,
)
index = build_peptide_protein_index(peptides)
uniqueness = classify_peptide_uniqueness(peptides)
duplicate_accounting = build_digest_duplicate_accounting(peptides)
policy_hash = compute_digest_policy_hash(policy)
```

The same digestion surface is available from the CLI with explicit export and
manifest outputs. The manifest snapshots the cleavage policy and a stable
policy hash so repeated runs can compare assumptions as well as peptide
payloads:

```bash
bijux-proteomics digest proteins.fasta \
  --protease trypsin \
  --missed-cleavages 1 \
  --digestion-mode full \
  --min-length 7 \
  --max-length 30 \
  --format jsonl \
  --out peptides.jsonl \
  --manifest-out digest.manifest.json
```

Peptide chemistry and modification handling are also first-class contracts in
the same package:

```python
from bijux_proteomics.chemistry import (
    approximate_peptide_isotope_envelope,
    build_modification_localization_advisory,
    build_modified_peptide,
    build_peptide_charge_state,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
)

peptide = build_modified_peptide(
    "PESTIDE",
    assignments=("Phospho@3", "Acetyl@n-term"),
)
canonical = canonicalize_modified_peptide(peptide)
charge_state = build_peptide_charge_state(peptide, charge=2)
fragments = calculate_fragment_ions(peptide, include_neutral_losses=True)
envelope = approximate_peptide_isotope_envelope(peptide, charge=2)
localization = build_modification_localization_advisory(peptide)
```

The same chemistry surface is also available from the CLI for quick mass,
fragment, isotope-envelope, and advisory localization checks:

```bash
bijux-proteomics peptide-mass PESTIDE \
  --mod Acetyl@n-term \
  --mod Phospho@3 \
  --charge 2 \
  --include-neutral-losses
```

Search-result normalization and PSM rollups are also first-class contracts in
the package:

```python
from pathlib import Path

from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    parse_psm_tsv,
    rollup_peptide_evidence,
    rollup_protein_evidence,
    select_best_psm_per_spectrum,
)

mapping = SearchResultColumnMapping(
    spectrum_id="spectrum_id",
    peptide="peptide",
    charge="charge",
    score="score",
    q_value="q_value",
    protein_refs="proteins",
)
report = parse_psm_tsv(Path("results.tsv"), mapping=mapping)
best_psms = select_best_psm_per_spectrum(report.accepted_records)
peptide_rollups = rollup_peptide_evidence(best_psms)
protein_rollups = rollup_protein_evidence(best_psms)
```

The same identification surface now covers basic target-decoy FDR, stable PSM
exports, and provenance capture:

```python
from pathlib import Path

from bijux_proteomics.identification import (
    FdrPolicy,
    SearchResultColumnMapping,
    TargetDecoyLabelPolicy,
    build_search_result_provenance_manifest,
    filter_psms_by_fdr,
    parse_psm_tsv,
)

mapping = SearchResultColumnMapping(
    spectrum_id="spectrum_id",
    peptide="peptide",
    charge="charge",
    score="score",
    protein_refs="proteins",
)
report = parse_psm_tsv(Path("results.tsv"), mapping=mapping)
accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.01)
manifest = build_search_result_provenance_manifest(
    source_path=Path("results.tsv"),
    parse_report=report,
    decoy_policy=TargetDecoyLabelPolicy(protein_prefix="DECOY_"),
    fdr_policy=FdrPolicy(threshold=0.01),
)
```

The CLI exposes the same workflow for inspection and thresholded export:

```bash
bijux-proteomics psm-inspect results.tsv \
  --jsonl-out normalized.jsonl \
  --provenance-out results.provenance.json

bijux-proteomics fdr results.tsv \
  --decoy-prefix DECOY_ \
  --threshold 0.01 \
  --jsonl-out accepted.jsonl \
  --provenance-out fdr.provenance.json
```

Label-free quantification is also available from the same package with stable
feature parsing, protein rollups, normalization, batch advisories, replicate
correlations, and basic differential abundance output:

```python
from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    NormalizationMethod,
    parse_ms1_feature_table,
    QuantEntityLevel,
    QuantRollupMethod,
)

feature_report = parse_ms1_feature_table(Path("ms1_features.tsv"))
design_report = parse_experimental_design_table(Path("quant.design.tsv"))
protein_table = build_label_free_intensity_table(
    feature_report.accepted_records,
    entity_level=QuantEntityLevel.PROTEIN,
    aggregation_method=QuantRollupMethod.TOP_N,
    top_n=2,
)
normalized = normalize_label_free_table(
    protein_table,
    method=NormalizationMethod.MEDIAN,
)
differential = apply_benjamini_hochberg(
    build_differential_abundance_report(
        normalized,
        design_report.accepted_entries,
        condition_a="control",
        condition_b="treatment",
    )
)
```

The same surface is available from the CLI for operator-facing quant reports:

```bash
bijux-proteomics quantify ms1_features.tsv \
  --design quant.design.tsv \
  --entity-level protein \
  --aggregation top_n \
  --top-n 2 \
  --normalization median \
  --condition-a control \
  --condition-b treatment \
  --report-out quant.report.json
```

See [docs/QUANTIFICATION.md](docs/QUANTIFICATION.md) for the full quantification
workflow and output semantics.

Spectrum and MGF handling are also first-class contracts in the package:

```python
from pathlib import Path

from bijux_proteomics.io.spectra import (
    annotate_spectrum_fragments,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    normalize_spectrum_peaks,
    parse_mgf,
)

report = parse_mgf(Path("spectra.mgf"))
spectrum = normalize_spectrum_peaks(report.accepted_spectra[0])
metrics = build_spectrum_metrics(spectrum)
annotation = annotate_spectrum_fragments(spectrum, peptide="PEPTIDE", tolerance_da=0.02)
plot_payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
```

The same spectrum surface is available from the CLI for file validation,
summary, provenance capture, and peptide-to-spectrum annotation:

```bash
bijux-proteomics spectrum-stats spectra.mgf \
  --provenance-out spectra.provenance.json

bijux-proteomics spectrum-annotate spectra.mgf \
  --peptide PEPTIDEK \
  --tsv-out annotation.tsv \
  --plot-out plot.json

bijux-proteomics validate spectra.mgf --kind mgf
bijux-proteomics summarize spectra.mgf --kind mgf
```

For a minimal end-to-end example that starts from FASTA, carries through
digest and search-result normalization, and finishes with FDR filtering plus
spectrum annotation, see
[`docs/FIRST_USEFUL_RUN.md`](./docs/FIRST_USEFUL_RUN.md).

Multi-format ingestion now also covers mzML, design tables, normalized format
conversion, and run-bundle materialization:

```bash
bijux-proteomics validate run.mzml --kind mzml
bijux-proteomics summarize experiment.design.tsv --kind design-table
bijux-proteomics format-convert run.mzml --kind mzml --to mgf --out run.converted.mgf
bijux-proteomics bundle-run \
  --spectra run.mzml \
  --identifications results.tsv \
  --design experiment.design.tsv \
  --out-dir bundle
```

That workflow is documented in
[`docs/FORMAT_INGESTION.md`](./docs/FORMAT_INGESTION.md).

Workflow-runtime planning is also available as a first-class operator surface:

```bash
bijux-proteomics workflow-plan \
  --proteins proteins.fasta \
  --spectra spectra.mgf \
  --identifications results.tsv \
  --features ms1_features.tsv \
  --design design.tsv \
  --sample-id sample-A \
  --search-adapter generic \
  --dag-out workflow.dag.json \
  --job-out workflow.slurm \
  --checkpoint-out workflow.checkpoint.json \
  --out workflow.bundle.json
```

That workflow is documented in
[`docs/WORKFLOW_RUNTIME.md`](./docs/WORKFLOW_RUNTIME.md).

Search-result adapters are also first-class now:

```bash
bijux-proteomics search-adapter inspect
bijux-proteomics search-adapter params comet comet.params

bijux-proteomics search-adapter normalize sage results.tsv \
  --adapter-version 0.16.0 \
  --config sage-config.json \
  --jsonl-out normalized.jsonl \
  --provenance-out adapter.provenance.json

bijux-proteomics search-adapter compare \
  sage results.tsv \
  generic results.tsv \
  --right-mapping-json sage-mapping.json

bijux-proteomics infer-proteins results.tsv \
  --threshold 0.05 \
  --fasta proteins.fasta
```

That workflow is documented in
[`docs/SEARCH_ADAPTERS.md`](./docs/SEARCH_ADAPTERS.md).
Protein inference is documented in
[`docs/PROTEIN_INFERENCE.md`](./docs/PROTEIN_INFERENCE.md).

PTM localization and site aggregation are also available from the same package:

```bash
bijux-proteomics ptm summarize localization_results.tsv proteins.fasta \
  --features ptm_features.tsv \
  --threshold 0.1 \
  --flank-size 3 \
  --out ptm.report.json
```

That workflow is documented in
[`docs/PTM_WORKFLOWS.md`](./docs/PTM_WORKFLOWS.md).

Run-level LC-MS QC and batch outlier diagnostics are also first-class
contracts:

```python
from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.spectra import parse_mgf
from bijux_proteomics.study.qc import (
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document

design = parse_experimental_design_table(Path("batch.design.tsv")).accepted_entries
fasta = parse_fasta_document(Path("proteins.fasta").read_text(), mode=FastaParseMode.STRICT)
protein_sequences = {
    record.canonical_accession: record.residues
    for record in fasta.accepted_records
}
mapping = SearchResultColumnMapping(
    spectrum_id="spectrum_id",
    peptide="peptide",
    charge="charge",
    score="score",
    protein_refs="proteins",
)

run_reports = []
for entry in design:
    spectra = parse_mgf(Path(entry.spectra_file)).accepted_spectra
    psms = parse_psm_tsv(Path(entry.identifications_file), mapping=mapping).accepted_records
    run_reports.append(
        build_lcms_run_qc_report(
            spectra,
            psms,
            design_entry=entry,
            protein_sequences=protein_sequences,
        )
    )

batch_report = build_instrument_batch_qc_report(tuple(run_reports))
```

Operator-facing QC reports are also available directly from the CLI:

```bash
bijux-proteomics qc report spectra.mgf results.tsv proteins.fasta \
  --design design.tsv \
  --policy qc_policy.json \
  --out qc.report.json \
  --tsv-out qc.metrics.tsv \
  --html-out qc.report.html \
  --manifest-out qc.evidence.json \
  --benchmark-out qc.benchmark.json
```

See [`docs/QC_OPERATOR_GUIDE.md`](./docs/QC_OPERATOR_GUIDE.md) for threshold
interpretation, advisory versus enforced findings, and failed-run diagnosis.

## Public APIs

The curated root API is intentionally narrow:

- `parse_fasta_document(...)` for durable protein-sequence intake
- `parse_experimental_design_table(...)` for governed study metadata
- `build_normalized_run_bundle(...)` for table-shaped evidence normalization
- `build_fdr_audit_trail(...)` for explicit score and q-value audit surfaces
- `DigestPolicy` for digestion assumptions that must survive export and rerun

Minimal executable example:

```python
from bijux_proteomics import parse_fasta_document

report = parse_fasta_document(">sp|P11111|PTM1 Protein 1\nMPEPTIDEK\n")

assert report.total_records == 1
assert len(report.accepted_records) == 1
assert report.accepted_records[0].canonical_accession == "P11111"
```

## Package identity

- Distribution name: `bijux-proteomics-core`
- Import root: `bijux_proteomics`
- Stable entrypoints: `domain`, `sequences`, `chemistry`, `identification`, `study`, `quantification`, `ptm`, `dia`, `review`, `workflow`, and `interfaces`

## Package boundaries

This package owns scientific meaning: domain models, evidence normalization,
uncertainty-aware review artifacts, and workflow contracts that preserve
proteomics semantics before execution and recommendation layers consume them.

It does not own provider binding, run orchestration, reference curation,
ranking policy, recommendation judgment, or lab scheduling behavior.

Core also does not pretend that one domain model solves the whole suite. It
defines the scientific source of truth, then hands execution, curation,
judgment, and operations outward to runtime, knowledge, intelligence, and lab.

## What this package must not do

- it must not own provider binding, API transport, or replay orchestration
- it must not replace knowledge curation, recommendation policy, or lab execution planning
- it must not hide lossy scientific normalization behind optimistic convenience wrappers

## Contract checkpoints

- scientific normalization must preserve mapped, unsupported, refused, and lost evidence states explicitly
- lifecycle transitions must flow through declared stage and gate rules
- repository and execution protocols must stay replaceable and runtime-agnostic
- downstream packages should consume core scientific rules instead of restating them

## Choose this package when

- you need canonical proteomics semantics that higher layers should consume rather than reinterpret
- the change defines evidence normalization, scientific ambiguity, or reviewable domain truth
- workflow contracts must stay runtime-agnostic while preserving scientific meaning

## Route elsewhere when

- the change defines provider behavior, reference curation, ranking policy, or lab operations
- the helper exists only to adapt core data into CLI, API, execution, or replay transport payloads
- the behavior is workflow-local glue instead of reusable scientific meaning

## Verification route

- check `tests` for lifecycle, validator, and protocol proof before treating a
  core change as safe
- review `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
  when ownership or contract claims are part of the change
- use `README.md`, `CHANGELOG.md`, and package `docs/*.md` when the change
  affects package publication, metadata, or release-readiness expectations

## Review questions

- does the change strengthen scientific meaning rather than execution, ranking, or operational transport
- would another package become the de facto owner of proteomics evidence semantics if this behavior stayed outside core
- can the change be justified without claiming runtime, knowledge, intelligence, or lab ownership

## Escalation route

- route the change outward when the behavior mainly shapes provider execution, reference curation, ranking policy, or lab operations
- stop and review `docs/BOUNDARIES.md` and `docs/ARCHITECTURE.md` when the proposal introduces workflow glue instead of reusable scientific law
- escalate before release when downstream packages would need to reinterpret core evidence semantics to adopt the change

## Consumer impact signals

- expect coordinated downstream review when evidence semantics, lifecycle rules, or workflow contracts change because higher layers consume that scientific meaning
- treat changes that alter normalization loss, refusal boundaries, or transition semantics as high-impact even when import paths stay stable
- expect a narrower release burden when the change only improves internal implementation without changing scientific outputs or contracts

## Explicit non-goals

- this package does not own runtime transport, provider binding, or replay orchestration
- this package does not own knowledge curation, ranking judgment, or lab workflow decisions
- this package does not exist to preserve stale compatibility wrappers that have no live consumer value

## Source guide

- [`src/bijux_proteomics/domain/program_spec.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/domain/program_spec.py) for canonical program entities and stage semantics
- [`src/bijux_proteomics/domain/programs.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/domain/programs.py) for review-gated progression and execution requests
- [`src/bijux_proteomics/sequences/core.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/sequences/core.py) for FASTA parsing, target-decoy generation, and sequence normalization
- [`src/bijux_proteomics/sequences/digestion.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/sequences/digestion.py) for protease rules, digestion modes, peptide filters, and peptide-to-protein indexing
- [`src/bijux_proteomics/chemistry/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/chemistry/__init__.py) for peptide masses, fragment ions, neutral losses, and modification semantics
- [`src/bijux_proteomics/identification/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/identification/__init__.py) for stable PSM parsing, target-decoy evaluation, and peptide/protein evidence rollups
- [`src/bijux_proteomics/identification/search_adapters.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/identification/search_adapters.py) for engine-specific manifests, normalization, conformance, and loss accounting
- [`src/bijux_proteomics/io/formats/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/io/formats/__init__.py) for format detection, mzML parsing, design-table support, and normalized run bundles
- [`src/bijux_proteomics/io/ingestion.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/io/ingestion.py) for mzIdentML, mzTab, mzML-decoding, chromatogram, and boundary-aware ingestion reports
- [`src/bijux_proteomics/io/spectra/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/io/spectra/__init__.py) for spectrum models, MGF parsing, fragment annotation, and plot payload export
- [`src/bijux_proteomics/quantification/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/quantification/__init__.py) for LFQ, multiplex, normalization, missingness, and DA-ready quant contracts
- [`src/bijux_proteomics/ptm/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/ptm/__init__.py) for PTM evidence parsing, site aggregation, site FDR, occupancy, and motif context
- [`src/bijux_proteomics/dia/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/dia/__init__.py) for DIA-native evidence, library validation, and targeted candidate export
- [`src/bijux_proteomics/review/__init__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/review/__init__.py) for contradiction-aware decision briefs and evidence-gap reporting
- [`src/bijux_proteomics/workflow/blueprint.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/workflow/blueprint.py) for runtime-agnostic scientific workflow blueprints
- [`src/bijux_proteomics/interfaces/runtime_plans.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/runtime_plans.py) for the explicit workflow-planning seam that imports runtime bundle validation without widening the core root
- [`src/bijux_proteomics/interfaces/execution/runtime_adapter.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/execution/runtime_adapter.py) for the explicit runtime adapter seam that keeps workflow execution ownership outside core
- [`src/bijux_proteomics/interfaces/examples.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/examples.py) for reader-facing digest, refusal, and loss-aware package examples
- [`src/bijux_proteomics/interfaces/cli/app.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/cli/app.py) and [`src/bijux_proteomics/interfaces/cli/__main__.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/cli/__main__.py) for package-owned contract workflows exposed through the core CLI entrypoint
- [`src/bijux_proteomics/study/qc.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/study/qc.py) for LC-MS run diagnostics, batch QC, and publication-threshold decisions
- [`src/bijux_proteomics/review/protein_family_graphs.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/review/protein_family_graphs.py) for contradiction-aware protein-family evidence projection
- [`src/bijux_proteomics/ptm/proteoforms.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/ptm/proteoforms.py) for canonical proteoform identity records anchored in PTM evidence
- [`src/bijux_proteomics/governance/charter.py`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/src/bijux_proteomics/governance/charter.py) for the machine-readable scientific domain map and boundary audit
- [`docs/FORMAT_INGESTION.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/FORMAT_INGESTION.md) for mzML, design-table, format-conversion, and run-bundle workflows
- [`docs/WORKFLOW_RUNTIME.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/WORKFLOW_RUNTIME.md) for workflow manifests, DAG projection, cache/artifact planning, scheduler export, and checkpoint semantics
- [`docs/PROTEIN_INFERENCE.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/PROTEIN_INFERENCE.md) for multi-level FDR, grouping, parsimony, picked protein FDR, and sequence-aware coverage workflows
- [`docs/PTM_WORKFLOWS.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/PTM_WORKFLOWS.md) for localized PTM evidence parsing, site aggregation, ambiguity reporting, site FDR, motif windows, enrichment export, and occupancy estimation
- [`docs/SEARCH_ADAPTERS.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/SEARCH_ADAPTERS.md) for engine-specific table normalization and adapter provenance workflows
- [`docs/FIRST_USEFUL_RUN.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/FIRST_USEFUL_RUN.md) for a copy-paste path from fixture inputs to thresholded reports and spectrum annotation
- [`docs/SHIPPED-DEMO-CLI.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/SHIPPED-DEMO-CLI.md) for the minimal shipped-demo CLI path from run to governed result validation and query
- [`docs/QC_OPERATOR_GUIDE.md`](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-core/docs/QC_OPERATOR_GUIDE.md) for threshold interpretation, advisory versus enforced QC findings, and failed-run diagnosis
- [`tests`](https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core/tests) for executable behavior expectations

## Documentation

- [Product architecture](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/product-architecture/)
- [Cross-package ownership](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/cross-package-ownership/)
- [Package guide](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/)
- [Ownership boundary](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/ownership-boundary/)
- [Architecture overview](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/)
- [Interface contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/)
- [Shipped demo CLI tutorial](docs/SHIPPED-DEMO-CLI.md)
- [Release and versioning](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/release-and-versioning/)
