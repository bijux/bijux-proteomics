---
title: Environment Model
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-07-21
---

# Environment model

Repository commands run through a shared Python 3.11 check environment beneath
`artifacts/root/check-venv`. Make centralizes tool selection, cache placement,
package paths, and strict shell behavior so local and CI runs share explicit
assumptions.

## Environment layout

| Variable or path | Default role |
| --- | --- |
| `PYTHON` | interpreter used to create environments; defaults to `python3.11` |
| `UV` | environment and dependency installer |
| `artifacts/root/check-venv` | shared repository check environment |
| `artifacts/root/pycache` | Python bytecode cache |
| `artifacts/root/xdg_cache` | XDG-compatible tool cache |
| `artifacts/root/hypothesis` | Hypothesis examples and state |
| `artifacts/root/uv_cache` | uv cache |
| `artifacts/root/npm_cache` | npm cache used by documentation or API tooling |
| `artifacts/<package>` | package-specific test, build, API, and SBOM output |

```mermaid
flowchart LR
    invoke["local or CI invocation"]
    root["root environment defaults"]
    overlay["repository overlay"]
    package["package profile paths"]
    check["tool or package command"]
    output["artifacts/ isolated output"]
    invoke --> root --> overlay --> package --> check --> output
```

## Prepare and inspect

```bash
make install
make root-check-env
make nlenv
```

`make install` synchronizes locked development groups into the shared
environment. `root-check-env` ensures the environment required by repository
gates exists. `nlenv` prints the activation command for interactive inspection;
activation is not required for normal Make targets.

Set `EXTRAS` to a comma-separated list only when a documented workflow requires
different uv groups. Use command-scoped overrides such as
`make docs PYTHON=python3.11` rather than depending on unrecorded shell state.

## Strict and isolated execution

Shared recipes use Bash with `-eu -o pipefail`, so unset variables and failed
pipeline stages are visible. Repository targets pass absolute monorepo,
configuration, project, API, and artifact paths into package execution. Shared
check targets also clear inherited cache variables before dispatch and provide
the repository-owned values.

Do not redirect caches into package source trees or rely on a globally active
virtual environment. Security audit commands intentionally clear
`VIRTUAL_ENV` where they need an explicit interpreter boundary.

## Reproducibility boundary

The environment model controls declared dependencies, paths, and command
composition. It cannot make external services, system libraries, hardware, or
network data identical. Tests that require those resources declare and record
them separately instead of treating one successful developer machine as the
portable environment contract.
