---
title: Compatibility Configuration
audience: mixed
type: reference
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Compatibility configuration

`agentic-proteins` owns no independent configuration schema. Its configuration
types and defaults are forwarded from `bijux-proteomics-runtime`; a legacy
import and a canonical import must construct the same object and produce the
same runtime behavior.

## Run configuration

`RunConfig` groups the decisions that must be recorded with an execution:

| Concern | Fields |
| --- | --- |
| Providers | `predictors_enabled`, `execution_mode` |
| Resource policy | `resource_limits`, `retry_policy`, `loop_max_cost` |
| Loop control | `loop_max_iterations`, `loop_stagnation_window`, `loop_improvement_threshold` |
| Reproducibility | `seed`, `tool_versions`, `dry_run`, `strict_mode` |
| Review | `require_human_decision`, `logging_enabled` |
| Placement | `artifacts_dir`, `launch_surface`, container and scheduler fields |
| Evidence capture | `max_bundle_artifact_bytes` |

Unknown fields are rejected. Calling `with_defaults()` returns both the
resolved configuration and a list naming every default that was applied. That
warning list matters: it distinguishes an operator choice from behavior
selected by the runtime.

```python
from agentic_proteins.orchestration.run_config import RunConfig

requested = RunConfig(
    predictors_enabled=["esmfold"],
    execution_mode="gpu",
    strict_mode=True,
    seed=11,
)
resolved, defaulted_fields = requested.with_defaults()
```

New code should import the same type from
`bijux_proteomics_runtime.runs.run_config`; the compatibility path exists for
consumer continuity.

## API configuration

`AppConfig` configures the forwarded FastAPI application. `base_dir` selects
the runtime workspace. `docs_enabled` controls OpenAPI, Swagger UI, and ReDoc;
`title`, `description`, and `version` describe the transport surface. Creating
the application does not validate scientific inputs or execute a workflow.

```python
from pathlib import Path

from agentic_proteins.interfaces.http import AppConfig, create_app

app = create_app(AppConfig(base_dir=Path("runtime-state"), docs_enabled=False))
```

There is no compatibility-only environment-variable namespace or hidden
configuration file. If the two package names resolve different defaults,
providers, workspace paths, or validation behavior, migration safety has been
broken.
