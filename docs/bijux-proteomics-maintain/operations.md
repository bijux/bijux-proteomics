# Operations

Use `make` targets from repository root for standard maintainer workflows.

`bijux-proteomics-dev` provides the implementation behind those commands so
operations stay consistent locally and in CI.

Core commands:

- `make quality` for docs checks and static quality gates
- `make api` for repository API schema lint, freeze, and drift checks
- `make api-freeze` for schema freeze integrity checks only
- `make security` for Bandit, pip-audit gating, and dependency policy checks
- `make openapi-drift` for OpenAPI backward-compatibility policy
- `make architecture-check` for repository architecture and debt guards
- `make manage_examples` and `make manage_models` for maintainer utility flows
