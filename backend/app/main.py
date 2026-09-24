import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import FetchError, InvalidInputError, ItemNotFoundError, ProviderError
from app.core.logging_config import configure_logging
from app.db.connection import init_db
from app.routers import ingest, items, logs, query
from app.routers import settings as settings_router

logger = logging.getLogger(__name__)
request_logger = logging.getLogger("app.request")

_ERROR_STATUS_MAP = {
    InvalidInputError: 400,
    ItemNotFoundError: 404,
    FetchError: 422,
    ProviderError: 502,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    init_db()
    logger.info("app.startup db=%s", settings.database_path)
    yield


app = FastAPI(title="AI Knowledge Inbox", lifespan=lifespan)


class SafetyNetMiddleware:
    """Catches anything the per-type handlers below don't recognize -- i.e.
    an actual bug, not one of our four domain errors -- and turns it into a
    normal JSON response instead of letting it reach Starlette's built-in
    ServerErrorMiddleware.

    That matters for two concrete reasons, both hit live during development
    (switching to a provider whose optional dependency wasn't installed):
    ServerErrorMiddleware sits *outside* CORSMiddleware, so its fallback
    response carries no CORS headers and the browser reports a generic
    "Failed to fetch" with zero information; and it also sits outside our
    own request-logging middleware, so the failure never reaches /logs.
    Catching the exception here -- positioned inside CORS in the middleware
    stack (see the add_middleware call order below) -- fixes both: our
    response passes through CORS and the request logger like any other.
    """

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception("request.unhandled_error path=%s", scope.get("path"))
            if response_started:
                raise  # can't send a fresh response, part of one already went out
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
            await response(scope, receive, send)


# Order matters: each add_middleware call makes that middleware the new
# outermost layer among these three, so adding SafetyNet first means it
# ends up innermost (closest to the routes) -- exactly where it needs to be
# to catch a bug before CORS/logging see it, so its response still passes
# through both normally afterward.
app.add_middleware(SafetyNetMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware:
    """Plain ASGI middleware, not @app.middleware("http")/BaseHTTPMiddleware --
    the latter re-raises exceptions instead of letting the exception_handler
    below convert them to a response (a known Starlette/BaseHTTPMiddleware
    interaction: https://github.com/encode/starlette/issues/1678).
    """

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        status_code_holder: dict[str, int] = {}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code_holder["status"] = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = (time.perf_counter() - started_at) * 1000
        request_logger.info(
            "request.completed method=%s path=%s status=%s duration_ms=%.1f",
            scope.get("method"),
            scope.get("path"),
            status_code_holder.get("status"),
            duration_ms,
        )


app.add_middleware(RequestLoggingMiddleware)


def _make_domain_error_handler(status_code: int):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        logger.warning("request.domain_error path=%s error=%s", request.url.path, exc)
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


# Registered per exception type (not the bare Exception class) so these go
# through Starlette's ExceptionMiddleware, which returns the response as-is.
# A handler on Exception itself gets routed to ServerErrorMiddleware instead,
# which *always* re-raises after responding -- correct for genuinely
# unexpected 500s (we want those loud in logs/tests), wrong for our own
# well-understood domain errors.
for error_type, status_code in _ERROR_STATUS_MAP.items():
    app.add_exception_handler(error_type, _make_domain_error_handler(status_code))


app.include_router(ingest.router)
app.include_router(items.router)
app.include_router(query.router)
app.include_router(settings_router.router)
app.include_router(logs.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
