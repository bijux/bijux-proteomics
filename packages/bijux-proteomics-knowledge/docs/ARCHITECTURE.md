# Architecture

## Package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`

## Architectural role

`bijux-proteomics-knowledge` provides scientific memory with provenance:
curated evidence, claims, contradiction handling, resolution history, and
grounded workflow references that downstream packages can inspect without
re-curating locally.

## Design constraints

- evidence records are first-class typed memory entities
- contradiction handling and resolution history stay explicit and auditable
- trust, freshness, and context completeness are measurable memory attributes
- curated references stay selective, cited, and workflow-scoped instead of becoming a generic context sink

## Module topology

- `memory/models/evidence.py` owns evidence bundles, provenance scoring, freshness, and contradiction inputs
- `memory/models/claims.py` owns claim state, lineage, and knowledge-gap modeling
- `memory/reconciliation/resolution.py` owns explicit conflict-resolution policies and resolution history
- `memory/integrity/graph.py` owns evidence-graph structure and validation
- `memory/normalization/ingestion.py` owns normalization of external evidence into knowledge-owned memory records
- `contracts/schema.py` owns schema compatibility and document contract profiles
- `identity/`, `features/`, `coverage/`, `pathways/`, `complexes/`,
  `kinases/`, `orthologs/`, `drugs/`, and `disease/` own reusable grounding,
  annotation, and biological-context resolution surfaces over curated memory
- `reviews/decision_briefs.py` owns decision-facing packets and multi-decision readiness summaries derived from existing scientific memory
- `reviews/explanations.py` owns decision-scoped graph explanations built from existing decision briefs
- `reviews/trends.py` owns packet comparisons and trend summaries for decision-facing change over time
- `references/grounding/` owns selective citations, contexts, corpora, ontologies, problems, and rules
- `references/workflows/` owns workflow briefings, benchmark manifests, workflow narratives, and the narrow workflow lookup surface
- `governance/` owns the machine-readable knowledge charter and owner-map
  boundaries for scientific memory, review, and grounding surfaces

## Canonical tree layout

- Import roots: `bijux_proteomics_knowledge`
- Top-level families: `complexes/`, `contracts/`, `coverage/`, `disease/`, `drugs/`, `features/`, `governance/`, `identity/`, `kinases/`, `memory/`, `orthologs/`, `pathways/`, `references/`, `reviews/`
- Root modules: `public_api.py`

## Dependency direction

The package is designed to keep scientific memory inspectable.

It may depend on foundation primitives and core identifiers, but it should not
take ownership of execution orchestration, route shaping, ranking or
recommendation policy, or lab execution logic.

## Downstream expectations

Downstream packages should use these memory and reference models directly
instead of maintaining separate evidence, provenance, contradiction, or lineage
formats.

## Extension signals

- add code here when a new concern changes evidence, claim, provenance,
  contradiction, resolution, or curated scientific-memory semantics
- extend `memory/`, `reviews/`, or `references/` before downstream packages create shadow memory models
- keep new auditability rules here when they define evidence meaning rather than only how a runtime or recommendation surface displays it

## Misplacement signals

- if the change needs execution orchestration, ranking or recommendation policy,
  lab scheduling, or transport-bound payload shaping, it belongs elsewhere
- if a helper mainly reformats evidence results for API or CLI consumers, it
  belongs in runtime adapters rather than in knowledge models
- if a rule only exists to serve one analytical or lab flow, keep it with that
  owner instead of making knowledge absorb workflow-specific behavior

## Review questions

- does the change alter canonical scientific memory, contradiction, lineage, or review semantics instead of only reformatting those outputs
- would another package create a shadow trust or resolution model if this behavior stayed out of knowledge
- can the architecture still be defended without claiming execution orchestration, ranking, recommendation, lab execution, or transport ownership
