# API Contracts

Repository API contracts live under `apis/<package>/v1/` for each main package.

Current package contract directories:

- `apis/agentic-proteins/v1`
- `apis/bijux-proteomics-foundation/v1`
- `apis/bijux-proteomics-core/v1`
- `apis/bijux-proteomics-intelligence/v1`
- `apis/bijux-proteomics-knowledge/v1`
- `apis/bijux-proteomics-lab/v1`

Each package contract directory includes:

- `schema.yaml` as the source OpenAPI contract
- `pinned_openapi.json` as the frozen canonical JSON rendering
- `schema.hash` as the SHA-256 digest of the pinned JSON
