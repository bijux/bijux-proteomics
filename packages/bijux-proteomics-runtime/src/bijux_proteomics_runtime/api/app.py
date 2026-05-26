# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""FastAPI app factory."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

from bijux_proteomics_runtime.api.errors import (
    ApiError,
    http_error,
    method_not_allowed,
    ok_envelope,
    validation_error,
)
from bijux_proteomics_runtime.api.request_logging import (
    RequestIdMiddleware,
    RequestLogMiddleware,
)
from bijux_proteomics_runtime.api.v1.router import router as v1_router
from bijux_proteomics_runtime.api.v1.schema import ApiEnvelope
from bijux_proteomics_runtime.providers.catalog import (
    provider_metadata,
    provider_requirements,
)
from bijux_proteomics_runtime.runs.correlation import (
    build_request_correlation_meta,
)
from bijux_proteomics_runtime.support.identity import (
    runtime_banner,
    runtime_description,
    runtime_title,
)


@dataclass(frozen=True)
class AppConfig:
    """AppConfig."""

    base_dir: Path
    docs_enabled: bool = True
    title: str = runtime_title()
    description: str = runtime_description()
    version: str = "2.0.0"


def create_app(config: AppConfig) -> FastAPI:
    """Create a configured FastAPI app.

    Inputs:
    ``config`` must provide the runtime base directory plus the app title,
    description, version, and documentation toggle policy.

    Outputs:
    Returns one configured ``FastAPI`` application with runtime middleware,
    exception handlers, provider metadata routes, and versioned API routers.

    Failure Modes:
    Propagates FastAPI router registration, middleware construction, and route
    handler setup failures during application assembly.

    Scientific Caveats:
    This factory assembles transport and operator wiring only; it does not
    validate scientific inputs or execute workflow algorithms at creation time.
    """
    docs_url = "/docs" if config.docs_enabled else None
    redoc_url = "/redoc" if config.docs_enabled else None
    openapi_url = "/openapi.json" if config.docs_enabled else None

    app = FastAPI(
        title=config.title,
        description=config.description,
        version=config.version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.base_dir = config.base_dir

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RequestLogMiddleware)

    @app.middleware("http")
    async def _method_guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Return 405 for unsupported methods on known routes."""
        scope = request.scope
        if scope.get("type") == "http":
            matched = False
            allowed_methods: set[str] = set()
            for route in app.router.routes:
                match, _ = route.matches(scope)
                if match in {Match.FULL, Match.PARTIAL}:
                    matched = True
                    route_methods = getattr(route, "methods", None)
                    if route_methods:
                        allowed_methods.update(route_methods)
            if matched and request.method not in allowed_methods:
                allow_header = ", ".join(sorted(allowed_methods))
                meta = build_request_correlation_meta(
                    request,
                    "method-guard",
                    request.url.path,
                )
                payload = method_not_allowed(
                    f"Method {request.method} not allowed.",
                    str(request.url),
                    meta=meta,
                )
                return JSONResponse(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    content=payload,
                    headers={"Allow": allow_header},
                )
        return await call_next(request)

    @app.exception_handler(ApiError)
    async def _handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        """_handle_api_error."""
        return JSONResponse(status_code=exc.status_code, content=exc.payload)

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """_handle_http_exception."""
        payload = http_error(
            exc.status_code,
            str(exc.detail),
            str(request.url),
            meta=build_request_correlation_meta(
                request, "http-error", request.url.path
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_starlette_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """_handle_starlette_http_exception."""
        payload = http_error(
            exc.status_code,
            str(exc.detail),
            str(request.url),
            meta=build_request_correlation_meta(
                request,
                "starlette-http-error",
                request.url.path,
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """_handle_validation_error."""
        payload = validation_error(
            str(exc),
            str(request.url),
            meta=build_request_correlation_meta(
                request,
                "validation-error",
                request.url.path,
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=payload
        )

    @app.get("/health", tags=["health"], response_model=ApiEnvelope)
    @app.get("/api/v1/health", tags=["health"], response_model=ApiEnvelope)
    def health(request: Request) -> dict[str, object]:
        """health."""
        return ok_envelope(
            {"status": "ok", "runtime": runtime_banner()},
            meta=build_request_correlation_meta(request, "health", "/health"),
        )

    @app.get("/ready", tags=["health"], response_model=ApiEnvelope)
    @app.get("/api/v1/ready", tags=["health"], response_model=ApiEnvelope)
    def ready(request: Request) -> dict[str, object]:
        """ready."""
        providers: dict[str, object] = {}
        try:
            for name in provider_metadata():
                providers[name] = {
                    "requirements": provider_requirements(name),
                }
            status_value = "ok"
        except Exception as exc:  # noqa: BLE001
            providers = {"error": [str(exc)]}
            status_value = "degraded"
        return ok_envelope(
            {
                "status": status_value,
                "runtime": runtime_banner(),
                "providers": providers,
            },
            meta=build_request_correlation_meta(request, "ready", "/ready"),
        )

    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app(AppConfig(base_dir=Path.cwd(), docs_enabled=True))
