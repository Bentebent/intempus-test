import logging

from fastapi import FastAPI

from config import Config


def create_api(config: Config, logger: logging.Logger) -> FastAPI:
    app = FastAPI()

    return app
