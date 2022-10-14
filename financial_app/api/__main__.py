from typing import Optional

from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics
from starlette_exporter.optional_metrics import response_body_size, request_body_size

from financial_app.settings import ServingSettings
from financial_app.data.sql.session import create_db_async_session_generator
from financial_app.api.routes.model import define_model_routes


def create_app(db_uri: Optional[str] = None):

    _app = FastAPI()

    _app.add_middleware(
        PrometheusMiddleware,
        group_paths=True,
        optional_metrics=[response_body_size, request_body_size]
    )

    _app.add_route("/metrics", handle_metrics)

    settings = ServingSettings()

    if db_uri is None:
        db_uri = settings.DB_URI

    try:
        get_session = create_db_async_session_generator(db_uri)
    except Exception:
        get_session = create_db_async_session_generator(settings.async_db_uri)

    _app.include_router(define_model_routes(get_session, settings), prefix="/model")

    return _app
