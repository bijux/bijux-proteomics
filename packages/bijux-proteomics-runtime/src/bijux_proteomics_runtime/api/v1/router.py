# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""API v1 router."""

from __future__ import annotations

from fastapi import APIRouter

from bijux_proteomics_runtime.api.v1.endpoints.compare import router as compare_router
from bijux_proteomics_runtime.api.v1.endpoints.inspect import router as inspect_router
from bijux_proteomics_runtime.api.v1.endpoints.resume import router as resume_router
from bijux_proteomics_runtime.api.v1.endpoints.run import router as run_router
from bijux_proteomics_runtime.api.v1.endpoints.runtime_contracts import (
    router as runtime_contract_router,
)

router = APIRouter()
router.include_router(run_router, tags=["run"])
router.include_router(resume_router, tags=["resume"])
router.include_router(inspect_router, tags=["inspect"])
router.include_router(compare_router, tags=["compare"])
router.include_router(runtime_contract_router, tags=["runtime-contracts"])
