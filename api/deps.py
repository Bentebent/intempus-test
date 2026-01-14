import logging
from typing import Annotated

import aiocache
from fastapi import Depends

import config
from db.db_client import DBClient
from shared.intempus_client import IntempusClient


@aiocache.cached()
async def get_config() -> config.Config:
    return config.Config()  # ty:ignore[missing-argument]


@aiocache.cached(ttl=60)
async def get_intempus_client(config: Annotated[config.Config, Depends(get_config)]) -> IntempusClient:
    return IntempusClient(config)


@aiocache.cached(ttl=60)
async def get_db_client(config: Annotated[config.Config, Depends(dependency=get_config)]) -> DBClient:
    return DBClient(config)


def get_logger_dep(logger: logging.Logger):
    def get_logger() -> logging.Logger:
        return logger

    return get_logger
