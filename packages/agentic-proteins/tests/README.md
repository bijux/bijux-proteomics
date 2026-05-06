# SPDX-License-Identifier: Apache-2.0  
# Copyright © 2025 Bijan Mousavi  

# Tests  

`agentic-proteins` is a strict compatibility package.
Its package-level proof should center on the surviving bridge families:
`tests/interfaces`, `tests/agents`, `tests/execution`, `tests/providers`,
`tests/state`, and `tests/tools`, with `tests/unit/compat` and
`tests/unit/governance` keeping the forwarding and boundary guards honest.

Legacy integration, regression, and real-local suites still exist because this
package remains a migration surface, but they do not redefine package
ownership.

## Test stratification  

- package validation should start with the mirrored bridge-family surfaces and
  the compatibility guards under `tests/unit/compat` and
  `tests/unit/governance`.  
- `make real-local` runs only `packages/agentic-proteins/tests/real_local` with the `real_local` marker.  

## Hardware expectations  

- `real_local` tests require local model weights; some require CUDA GPUs.  
- CPU-only real-local tests are marked `slow` and can take minutes.  
