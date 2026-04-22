# SPDX-License-Identifier: Apache-2.0  
# Copyright © 2025 Bijan Mousavi  

# Tests  

`agentic-proteins` is a strict compatibility package.
Its package-level CI runs forwarding-surface checks only from `tests/unit/compat`.
Legacy runtime and domain tests remain in this tree as migration history and are not
the release gate for the compat package.

## Test stratification  

- `make test` runs compatibility tests in `tests/unit/compat`.  
- `make real-local` runs only `packages/agentic-proteins/tests/real_local` with the `real_local` marker.  

## Hardware expectations  

- `real_local` tests require local model weights; some require CUDA GPUs.  
- CPU-only real-local tests are marked `slow` and can take minutes.  
