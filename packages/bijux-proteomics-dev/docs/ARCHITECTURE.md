# Architecture

The package is organized by maintenance domains:

- `quality` for linting and repository quality checks
- `security` for vulnerability and dependency policy gates
- `api` for OpenAPI contract drift checks
- `release` for version and changelog checks
- `docs` for documentation consistency checks
- `tools` for maintainers-only operational helpers

API governance helpers treat `apis/<package>/v1/` as the contract root and
enforce:

- schema lint validity (`schema.yaml`)
- freeze integrity (`pinned_openapi.json` and `schema.hash`)
- backward-compatibility checks across package schemas
