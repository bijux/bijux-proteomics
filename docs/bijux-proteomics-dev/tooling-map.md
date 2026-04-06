# Tooling Map

`bijux-proteomics-dev` provides the implementation behind root maintenance
commands.

| Maintainer command | Module entrypoint |
| --- | --- |
| `make docs-links` | `python -m bijux_proteomics_dev.docs.markdown_links` |
| `make quality` docs consistency step | `python -m bijux_proteomics_dev.docs.consistency` |
| `make openapi-drift` | `python -m bijux_proteomics_dev.api.openapi_drift` |
| `make architecture-check` invariants step | `python -m bijux_proteomics_dev.docs.architecture_docs` |
| `make architecture-check` design debt step | `python -m bijux_proteomics_dev.docs.design_debt` |
| `make security` pip-audit gate | `python -m bijux_proteomics_dev.security.pip_audit_gate` |
| `make security` dependency allowlist | `python -m bijux_proteomics_dev.security.dependency_allowlist` |
| `make manage_examples` | `python -m bijux_proteomics_dev.tools.manage_examples` |
| `make manage_models` | `python -m bijux_proteomics_dev.tools.manage_models` |
