# SPDX-License-Identifier: Apache-2.0  
# Copyright © 2025 Bijan Mousavi  

# Tests  

## Test stratification  

- `make test` runs all tests except `real_local` (the default pytest addopts exclude them).  
- `make real-local` runs only `packages/agentic-proteins/tests/real_local` with the `real_local` marker.  

## Hardware expectations  

- `real_local` tests require local model weights; some require CUDA GPUs.  
- CPU-only real-local tests are marked `slow` and can take minutes.  
