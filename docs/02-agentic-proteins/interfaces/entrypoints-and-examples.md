---
title: Compatibility Entrypoints
audience: mixed
type: how-to
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-07-21
---

# Compatibility entrypoints

Use these entrypoints only while migrating an existing `agentic-proteins`
consumer. New integrations should use the canonical runtime distribution.

## Command line

The historical and canonical commands expose the same Click command group:

```bash
# Historical
agentic-proteins run --sequence MKTIIALSYIFCLVFADYKDDDDK --dry-run --json

# Canonical
bijux-proteomics-runtime run --sequence MKTIIALSYIFCLVFADYKDDDDK --dry-run --json
```

Migrate scripts by changing the executable name, then compare exit status,
structured output, and produced artifact hashes under the same pinned package
versions. Commands include `run`, `resume`, `compare`, `reproduce`,
`inspect-candidate`, `import-result`, `export-report`, `identity`, and `api`.

## Python execution

```python
# Historical
from agentic_proteins.execution.manager import RunManager

# Canonical
from bijux_proteomics_runtime.runs.manager import RunManager
```

Provider, tool, state, planning, evaluation, and agent imports follow the same
pattern, but some historical families split across more precise canonical
owners. Use the generated migration guide rather than replacing only the top
package name mechanically.

## HTTP application

```python
# Historical
from agentic_proteins.interfaces.http.app import create_app

# Canonical
from bijux_proteomics_runtime.api.app import create_app
```

After changing imports, compare the pinned OpenAPI schemas in
`apis/agentic-proteins/v1/` and `apis/bijux-proteomics-runtime/v1/`. Route
availability alone is insufficient; request fields, response fields, status
codes, and failure bodies are part of the client contract.

## Structure reports

```python
# Historical
from agentic_proteins.interfaces.structure_reports import Report, to_text

# Canonical scientific owner
from bijux_proteomics.review.structure_reports import Report
from bijux_proteomics.review.structure_reports.render import to_text
```

This exception maps to core because structure-report meaning is scientific,
not an execution concern.

## Migration checklist

1. Inventory imported modules, executable names, and HTTP routes.
2. Resolve each module through the
   [canonical migration guide](../../09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-canonical-migration-guide.md).
3. Pin bridge and canonical packages to compatible releases.
4. Run consumer tests against both paths and compare persisted artifacts.
5. Update deployment commands, type-checker configuration, and API clients.
6. Remove `agentic-proteins` only after no supported caller uses its imports or
   executable.

Do not add fallback imports that silently choose whichever package happens to
be installed. That hides dependency mistakes and makes retirement impossible
to verify.
