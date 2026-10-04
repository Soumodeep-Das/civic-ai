from contextlib import asynccontextmanager
import json
import logging
import os
import re
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from civicai.auth import DUMMY_PASSWORD_HASH, LoginThrottle
from civicai.config import auth_settings, database_url, email_settings, evidence_settings, geocoding_settings, oidc_settings, runtime_settings
from civicai.database import build_engine
from civicai.domain import AssignmentConflict, ComplaintNotFound, DepartmentNotFound, InvalidStatusTransition, StaleComplaintUpdate
from civicai.geocoding import Geocoder, GeocodingUnavailable, MapTilerGeocoder, NominatimGeocoder
from civicai.routes import router
from civicai.identity_routes import identity_router
from civicai.emailing import build_email_service
from civicai.evidence import LocalEvidenceStorage, build_evidence_storage
from civicai.oidc import GoogleOIDCClient
from civicai.uploads import upload_directory
from starlette.exceptions import HTTPException

LOGGER = logging.getLogger("civicai.requests")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def create_app(url: str | None = None, geocoder: Geocoder | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.runtime_settings = runtime_settings()
        app.state.engine = build_engine(url or database_url())
        app.state.upload_directory = upload_directory()
        app.state.evidence_storage = build_evidence_storage(evidence_settings())
        app.state.auth_settings = auth_settings()
        app.state.login_throttle = LoginThrottle()
        app.state.identity_throttle = LoginThrottle(limit=5, window_seconds=600)
        app.state.dummy_password_hash = DUMMY_PASSWORD_HASH
        app.state.email_service = build_email_service(email_settings())
        app.state.oidc_settings = oidc_settings()
        app.state.oidc_client = GoogleOIDCClient(app.state.oidc_settings)
        settings = geocoding_settings()
        if geocoder is not None:
            app.state.geocoder = geocoder
        elif settings.provider == "maptiler":
            app.state.geocoder = MapTilerGeocoder(
                settings.maptiler_base_url, settings.maptiler_api_key,
                settings.country_codes, settings.proximity, settings.maptiler_request_origin,
            )
        elif settings.provider == "nominatim":
            app.state.geocoder = NominatimGeocoder(
                settings.base_url, settings.user_agent, settings.country_codes
            )
        else:
            raise RuntimeError("GEOCODING_PROVIDER must be 'nominatim' or 'maptiler'")
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title="CivicAI", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    app.include_router(identity_router)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        supplied = request.headers.get("x-request-id", "")
        request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else uuid4().hex
        request.state.request_id = request_id
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        if request.url.path.startswith(("/api/", "/health", "/ready")):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        elif request.app.state.runtime_settings.environment in {"production", "beta"}:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; "
                "object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob: https://api.maptiler.com https://*.maptiler.com; "
                "connect-src 'self' https://api.maptiler.com https://*.maptiler.com; "
                "font-src 'self' data:; worker-src 'self' blob:"
            )
        if request.app.state.runtime_settings.environment in {"production", "beta"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.url.path.startswith(("/api/v1/auth", "/api/v1/citizen", "/api/v1/staff", "/api/v1/admin")):
            response.headers["Cache-Control"] = "no-store"
        LOGGER.info(json.dumps({
            "event": "http_request", "request_id": request_id,
            "method": request.method, "route": getattr(request.scope.get("route"), "path", "unmatched"),
            "status": response.status_code, "duration_ms": round((perf_counter() - started) * 1000, 2),
        }, separators=(",", ":")))
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={
            "code": "validation_error" if exc.status_code in (400, 413, 422) else "request_error",
            "message": str(exc.detail),
        })

    @app.get("/health")
    def health(request: Request):
        return {"status": "ok", "release": request.app.state.runtime_settings.release_id}

    @app.get("/ready")
    def ready(request: Request):
        try:
            storage = request.app.state.evidence_storage
            storage_ready = storage.ready()
            if isinstance(storage, LocalEvidenceStorage):
                storage_ready = storage_ready and os.access(storage.directory, os.R_OK | os.W_OK)
        except Exception:
            storage_ready = False
        if not storage_ready:
            return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "evidence_storage"})
        try:
            with request.app.state.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
        except Exception:
            return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database"})
        if revision != "0008":
            return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "schema"})
        return {"status": "ready", "release": request.app.state.runtime_settings.release_id}

    @app.exception_handler(ComplaintNotFound)
    async def missing(request: Request, exc: ComplaintNotFound):
        return JSONResponse(status_code=404, content={"code": "complaint_not_found", "message": "Complaint not found"})

    @app.exception_handler(InvalidStatusTransition)
    async def invalid_transition(request: Request, exc: InvalidStatusTransition):
        return JSONResponse(status_code=409, content={
            "code": "invalid_status_transition",
            "message": f"A complaint cannot move from {exc.current.value} to {exc.requested.value}.",
        })

    @app.exception_handler(StaleComplaintUpdate)
    async def stale_update(request: Request, exc: StaleComplaintUpdate):
        return JSONResponse(status_code=409, content={
            "code": "stale_complaint_update",
            "message": "This complaint was changed by another municipal user. Refresh the latest information before changing it.",
        })

    @app.exception_handler(AssignmentConflict)
    async def assignment_conflict(request: Request, exc: AssignmentConflict):
        return JSONResponse(status_code=409, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(DepartmentNotFound)
    async def department_missing(request: Request, exc: DepartmentNotFound):
        return JSONResponse(status_code=404, content={"code": "department_not_found", "message": "Department not found"})

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, exc: RequestValidationError):
        details = [{"location": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"code": "validation_error", "message": "Invalid request", "details": details})

    @app.exception_handler(OperationalError)
    async def unavailable(request: Request, exc: OperationalError):
        return JSONResponse(status_code=503, content={"code": "database_unavailable", "message": "Database temporarily unavailable"})

    @app.exception_handler(GeocodingUnavailable)
    async def geocoding_unavailable(request: Request, exc: GeocodingUnavailable):
        return JSONResponse(status_code=503, content={
            "code": "location_search_unavailable",
            "message": "Location search is temporarily unavailable. Your complaint draft is safe; please try again.",
        })

    frontend = os.environ.get("FRONTEND_DIST_DIR", "").strip()
    if frontend:
        root = Path(frontend).resolve()

        @app.get("/{requested_path:path}", include_in_schema=False)
        def frontend_route(requested_path: str):
            if requested_path.startswith(("api/", "health", "ready")):
                raise HTTPException(404, "Not found")
            candidate = (root / requested_path).resolve()
            if requested_path and candidate.is_relative_to(root) and candidate.is_file():
                return FileResponse(candidate, headers={"Cache-Control": "public, max-age=31536000, immutable" if requested_path.startswith("assets/") else "no-cache"})
            index = root / "index.html"
            if index.is_file():
                return FileResponse(index, headers={"Cache-Control": "no-store"})
            raise HTTPException(404, "Frontend not found")

    return app


app = create_app()
