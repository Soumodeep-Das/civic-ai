from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from civicai.config import database_url, geocoding_settings
from civicai.database import build_engine
from civicai.domain import ComplaintNotFound
from civicai.geocoding import Geocoder, GeocodingUnavailable, MapTilerGeocoder, NominatimGeocoder
from civicai.routes import router
from civicai.uploads import upload_directory
from starlette.exceptions import HTTPException


def create_app(url: str | None = None, geocoder: Geocoder | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = build_engine(url or database_url())
        app.state.upload_directory = upload_directory()
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
