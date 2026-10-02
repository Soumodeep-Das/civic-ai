from contextlib import asynccontextmanager
import json
import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from civicai.auth import LoginThrottle
from civicai.config import auth_settings, database_url, geocoding_settings
from civicai.database import build_engine
from civicai.domain import AssignmentConflict, ComplaintNotFound, DepartmentNotFound, InvalidStatusTransition, StaleComplaintUpdate
from civicai.geocoding import Geocoder, GeocodingUnavailable, MapTilerGeocoder, NominatimGeocoder
from civicai.routes import router
from civicai.uploads import upload_directory
from starlette.exceptions import HTTPException

LOGGER = logging.getLogger("civicai.requests")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def create_app(url: str | None = None, geocoder: Geocoder | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = build_engine(url or database_url())
        app.state.upload_directory = upload_directory()
        app.state.auth_settings = auth_settings()
        app.state.login_throttle = LoginThrottle()
        settings = geocoding_settings()
        if geocoder is not None:
            app.state.geocoder = geocoder
        elif settings.provider == "maptiler":
            app.state.geocoder = MapTilerGeocoder(
                settings.maptiler_base_url, settings.maptiler_api_key,
                settings.country_codes, settings.proximity,
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
        if request.url.path.startswith(("/api/v1/auth", "/api/v1/admin")):
            response.headers["Cache-Control"] = "no-store"
        LOGGER.info(json.dumps({
            "event": "http_request", "request_id": request_id,
            "method": request.method, "path": request.url.path,
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
    def health():
        return {"status": "ok"}

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

    return app


app = create_app()
