# Boundaries

This boundary contract is mandatory for runtime migration and follow-on work.

## Package identity

- Distribution name: `bijux-proteomics-runtime`
- Import root: `bijux_proteomics_runtime`

## Allowed dependencies

`bijux-proteomics-runtime` may depend on:

- `bijux-proteomics-foundation`
- `bijux-proteomics-core`
- `bijux-proteomics-knowledge`
- `bijux-proteomics-intelligence`
- `bijux-proteomics-lab`

## This package owns

This package owns:

- interfaces (CLI and HTTP API)
- execution control and orchestration coordination
- provider binding and provider invocation
- runtime state transitions
- workspace state and run artifacts
- replay and determinism enforcement

## This package does not own

This package does not own:

- canonical domain definitions
- evidence semantics and contradiction semantics
- scoring policy semantics and recommendation semantics
- lab planning semantics and experiment promotion semantics

## Canonical ownership matrix

- `bijux-proteomics-foundation`: identifiers, schemas, canonical serialization, and shared error primitives
- `bijux-proteomics-core`: domain models, lifecycle semantics, and runtime-agnostic execution contracts
- `bijux-proteomics-knowledge`: evidence records, claims, trust semantics, and conflict resolution semantics
- `bijux-proteomics-intelligence`: scoring, ranking, policy, and recommendation semantics
- `bijux-proteomics-lab`: experiment planning and outcome promotion semantics
- `bijux-proteomics-runtime`: runtime orchestration, interfaces, providers, state machines, and run artifacts

## Dependency direction law

Lower layers must not import runtime modules.

The following package families must not import `bijux_proteomics_runtime`:

- `bijux_proteomics_foundation*`
- `bijux_proteomics*` (core)
- `bijux_proteomics_knowledge*`
- `bijux_proteomics_intelligence*`
- `bijux_proteomics_lab*`

Runtime adapts lower layers. Lower layers remain runtime-agnostic.

## Adapter rule

Runtime must use adapter and mapper modules when translating lower-layer domain
objects into runtime interface payloads. Lower layers must not expose runtime
shapes or import runtime contracts.

## Supported execution surfaces

- `launch_surface="local"` is the canonical direct execution surface
- `launch_surface="container"` is limited to replay-safe bundle and digest capture
- `launch_surface="scheduler"` is limited to replay-safe scheduler submission metadata
- `launch_surface="import"` is limited to provenance-preserving external result normalization
- `execution_mode="auto"` may choose CPU after provider capability checks
- `execution_mode="cpu"` is the supported CPU-compatible mode
- `execution_mode="gpu"` is supported only when provider capabilities and environment support agree

Runtime does not own container image build policy, cluster provisioning, queue
policy, or scientific derivation claims for imported evidence.

## Downstream expectations

Downstream callers should treat runtime as the canonical owner of
orchestration, provider binding, and operator-facing entrypoints, while in-repo
and package-internal consumers should import exact owners such as `api.app`,
`runs.manager`, `runs.preflight`, `runs.import_lineage`, `workflows.paths`,
`providers.catalog`, and `providers.selection`.

Lower layers should stay meaningful without importing runtime shapes.

## Migration staging law

During staged migration from `agentic-proteins`, canonical runtime surfaces must
land in `bijux-proteomics-runtime` first, then legacy `agentic-proteins` module
paths become compatibility forwarders.

Compatibility package modules are not canonical ownership surfaces.
Compatibility package modules are forwarding-only surfaces in strict mode.

## Escalation signals

- if a change introduces a new operator entrypoint, provider binding surface, or
  execution-product contract, it should start here before compat forwards it
- if a proposed runtime change requires new schema, lifecycle, evidence,
  ranking, or lab meaning, escalate it back to the owning lower package first
- if a lower-layer package needs to import runtime to express its own domain
  truth, treat that as a boundary failure and redesign the seam instead

## Boundary failure signals

- if lower-layer packages start importing runtime modules to express their own
  semantics, runtime is owning too much and the seam needs to move downward
- if compat modules become the first landing place for canonical runtime
  behavior, migration staging has drifted and ownership must be pulled back here
- if runtime adapters have to redefine schema, lifecycle, evidence, ranking, or
  lab truth locally, the owning lower package contract is incomplete
- if runtime docs teach internal consumers to start from `bijux_proteomics_runtime`
  instead of the actual owner modules, boundary clarity has regressed

## Review questions

- does the change alter canonical operator entrypoints, provider binding,
  execution coordination, or replay-safe runtime behavior
- would compat or lower packages start carrying runtime-local orchestration or
  transport truth if this concern stayed out of runtime
- can the change still be defended without masking a missing contract in a
  lower owning package
