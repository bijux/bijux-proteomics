# bijux-proteomics-runtime

`bijux-proteomics-runtime` is the canonical runtime package for execution
orchestration in the proteomics package family.

It owns runtime control surfaces (CLI, API, provider binding, replay,
determinism, and runtime workspace/artifact lifecycle) while depending on lower
packages for domain meaning.

Runtime uses explicit adapter modules for lower-package contracts and keeps
domain ownership in canonical lower layers:

- `core`: biology, sequence, and structure semantics
- `knowledge`: confidence, evidence, and trust semantics
- `intelligence`: candidate scoring, ranking, and loop policy semantics
- `lab`: experiment planning and outcome promotion semantics

## Package docs

- [Architecture](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/ARCHITECTURE.md)
- [Boundaries](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/BOUNDARIES.md)
- [Contracts](https://github.com/bijux/bijux-proteomics/blob/main/packages/bijux-proteomics-runtime/docs/CONTRACTS.md)
