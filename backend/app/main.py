import json
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from traceback import extract_tb
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.formparsers import MultiPartException

from .api import router
from .config import Settings
from .context import request_id as current_request_id
from .correction_api import router as correction_router
from .db import make_engine
from .errors import DomainError
from .resolution_api import router as resolution_router
from .rules import MAX_BYTES
from .security import Crypto

logger = logging.getLogger("apaar.requests")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


class BodyLimit:
    """Bound multipart spooling as well as the endpoint's file read."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        received = 0
        limit = MAX_BYTES + 65536
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = limit + 1
        if declared > limit:
            return await JSONResponse(
                {"code": "FILE_SIZE", "message": "Request exceeds the demo upload limit", "details": []},
                status_code=413,
            )(scope, receive, send)

        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise MultiPartException("Request exceeds the demo upload limit")
            return message

        await self.app(scope, bounded_receive, send)


def create_app(settings: Settings | None = None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings
        app.state.engine = make_engine(settings.database_url.get_secret_value())
        app.state.crypto = Crypto(settings)
        app.state.login_attempts = defaultdict(list)
        yield
        app.state.engine.dispose()

    app = FastAPI(title="APAAR admission workspace — simulated registry", version="0.1.0", lifespan=lifespan)
    app.add_middleware(BodyLimit)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )

    @app.middleware("http")
    async def request_headers(request: Request, call_next):
        started = perf_counter()
        request_id = str(uuid4())
        context_token = current_request_id.set(request_id)
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 -- final boundary logs safe locations, never exception values
            logger.error(
                json.dumps(
                    {
                        "event": "unexpected_error",
                        "request_id": request_id,
                        "exception_type": type(exc).__name__,
                        "frames": [
                            {"file": Path(f.filename).name, "line": f.lineno, "function": f.name}
                            for f in extract_tb(exc.__traceback__)
                        ],
                    }
                )
            )
            response = JSONResponse(
                {
                    "code": "INTERNAL_ERROR",
                    "message": "Unexpected error. Use the request ID when reporting this issue",
                    "details": [],
                },
                status_code=500,
            )
        finally:
            current_request_id.reset(context_token)
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        route = request.scope.get("route")
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "route": getattr(route, "path", "unmatched"),
                    "status": response.status_code,
                    "duration_ms": round((perf_counter() - started) * 1000, 1),
                }
            )
        )
        return response

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse(
            {"code": exc.code, "message": exc.message, "details": exc.details}, status_code=exc.status
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        details = [{"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            {"code": "VALIDATION_ERROR", "message": "Check the submitted fields", "details": details},
            status_code=422,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse(
            {
                "code": "DATA_CONFLICT",
                "message": "A duplicate or concurrent change was detected. Refresh and try again",
                "details": [],
            },
            status_code=409,
        )

    @app.exception_handler(OperationalError)
    async def database_error(request, exc):
        return JSONResponse(
            {
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database unavailable. Try again later",
                "details": [],
            },
            status_code=503,
        )

    app.include_router(router)
    app.include_router(resolution_router)
    app.include_router(correction_router)
    return app


app = create_app()
