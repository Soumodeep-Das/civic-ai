from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from civicai.config import database_url
from civicai.database import build_engine
from civicai.domain import ComplaintNotFound
from civicai.routes import router


def create_app(url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = build_engine(url or database_url())
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title="CivicAI", version="0.1.0", lifespan=lifespan)
    app.include_router(router)

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

    return app


app = create_app()
