import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from . import deps, routes


def create_api(logger: logging.Logger) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[routes.get_logger] = deps.get_logger_dep(logger)

    @app.middleware("http")
    async def logging_exception_middleware(request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")

        try:
            response = await call_next(request)
            return response
        except HTTPException as exc:
            logger.error(f"HTTPException: {exc.status_code} {exc.detail}", exc_info=True)
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.status_code,
                        "detail": exc.detail,
                    }
                },
            )

        except Exception as exc:
            logger.error(f"Exception: {exc.__class__.__name__}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "detail": "An unhandled exception occurred.",
                    }
                },
            )

    routes.append_routes(app)
    return app
