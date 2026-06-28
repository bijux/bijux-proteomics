# Architecture

## Package identity

- Distribution name: `bijux-proteomics-core`
- Import root: `bijux_proteomics`

## Architectural role

`bijux-proteomics-core` models the scientific heart of the suite: program
semantics, evidence normalization, review artifacts, study contracts, and
runtime-agnostic workflow seams.

## Design constraints

- domain entities are explicit and strongly typed
- review and lifecycle rules are model-level invariants
- runtime integration stays behind explicit interface seams

## Module topology

- `domain/` owns canonical program semantics: targets, constraints, context,
  criteria, liabilities, lifecycle, review gates, and validation
- `biology/` owns biological regulator, pathway, protein-agent, and signal
  semantics that stay below runtime orchestration and above raw chemistry
- `sequences/` and `chemistry/` own peptide, digest, isotope, and modification
  semantics
- `io/` and `identification/` own normalized evidence ingestion and
  identification contracts
- `quantification/`, `study/`, `ptm/`, and `dia/` own quantitative, laboratory,
  PTM, and DIA scientific meaning
- `interpretation/` owns typed scientific interpretation helpers over already-normalized core evidence
- `isotope_labeling/`, `multiplex/`, and `targeted/` own label-aware, multiplexed, and targeted assay scientific contracts
- `lab/` owns core-side laboratory design and review models that remain runtime-agnostic
- `panels/` and `proteoforms/` own panel-facing and proteoform-specific scientific result surfaces
- `review/` owns decision briefs, collaboration bundles, and structure-report
  surfaces
- `workflow/` owns scientific workflow blueprints
- `interfaces/` owns runtime-facing seams, reader-facing examples, Python API
  command runners, CLI boundaries, and compatibility registries for
  interface-owned helper modules
- `benchmarks/` owns packaged corpus, adoption, and benchmark evidence surfaces
- `governance/` owns the machine-readable package charter and owner-map
  boundaries for core scientific surfaces

## Canonical tree layout

- Import roots: `bijux_proteomics`
- Top-level families: `benchmarks/`, `biology/`, `chemistry/`, `dia/`, `domain/`, `governance/`, `identification/`, `interfaces/`, `interpretation/`, `io/`, `isotope_labeling/`, `lab/`, `multiplex/`, `panels/`, `proteoforms/`, `ptm/`, `quantification/`, `review/`, `sequences/`, `study/`, `targeted/`, `workflow/`
- Root modules: `_atomic_files.py`, `_output_tables.py`, `_scientific_tables.py`, `_tabular.py`, `programs.py`, `public_api.py`, `scientific_tables.py`, `tabular.py`

## Interface boundaries

- `bijux_proteomics.interfaces` is a curated package-root example surface for
  reader-facing scientific walkthroughs
- `bijux_proteomics.interfaces.python_api` is the programmatic runner surface
  for package-owned command execution
- `bijux_proteomics.interfaces.cli` owns the interactive CLI entrypoint and
  command grouping
- `bijux_proteomics.interfaces.support` and
  `bijux_proteomics.interfaces.cli.support` are compatibility registries for
  support submodules, not the preferred internal import target
- internal interface code should import owner modules such as
  `foundation`, `identification`, `interpretation`, `io_and_dia`,
  `multiplex_targeted`, `ptm_quantification`, `review_sequences_study`, and
  `workflow` directly instead of reaching through a root support barrel

## Dependency direction

The package is designed as the durable semantic source of truth for progression
and review behavior.

Higher layers may depend on this package for canonical program meaning, but
this package should not absorb evidence trust, ranking policy, or laboratory
execution semantics.

## Downstream expectations

Downstream packages should use these models and validators instead of
recreating lifecycle logic in runtime, intelligence, or lab-specific helpers.

## Extension signals

- add code here when a new concern changes canonical scientific meaning,
  evidence normalization, review artifacts, or runtime-agnostic workflow seams
- extend `domain/program_spec.py`, `domain/validation.py`, or `domain/repositories.py` before higher
  packages recreate lifecycle rules locally
- keep new domain invariants here when they define program truth rather than a
  package-specific execution policy

## Misplacement signals

- if the change needs evidence trust, candidate ranking, lab scheduling, or
  operator transport wiring, it belongs in a different package
- if a helper mainly reshapes core state for transport or execution, it belongs
  in runtime or interface seams rather than core scientific owners
- if the rule only exists to support one higher-layer recommendation workflow,
  keep it with that owner instead of making core absorb it

## Review questions

- does the change alter canonical lifecycle meaning, review gates, or
  runtime-agnostic execution protocols
- would higher packages become the de facto source of truth for progression
  rules if this behavior stayed out of core
- can the architecture still be described without relying on runtime transport,
  evidence semantics, or lab-local workflow exceptions
