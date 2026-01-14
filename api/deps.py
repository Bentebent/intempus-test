"""
FastAPI dependency providers for shared application resources.

This module defines reusable dependencies for configuration, database access,
Intempus API access, and logging. Dependencies are cached to avoid unnecessary
re-initialization and to improve request performance.

Caching:
    - Configuration is cached indefinitely.
    - Database and Intempus clients are cached with a TTL to allow refresh.
"""

import logging
from typing import Annotated

import aiocache
from fastapi import Depends

import config
from db.db_client import DBClient
from shared.intempus_client import IntempusClient


@aiocache.cached()
async def get_config() -> config.Config:
    """
    Load and cache application configuration.

    Returns:
        Config: Application configuration loaded from environment variables.

    Notes:
        - The result is cached indefinitely to avoid repeated config parsing.
        - Configuration includes database settings and Intempus API credentials.
    """
    return config.Config()  # ty:ignore[missing-argument]


@aiocache.cached(ttl=60)
async def get_intempus_client(config: Annotated[config.Config, Depends(get_config)]) -> IntempusClient:
    """
    Provide a cached Intempus API client.

    Args:
        config (Config): Application configuration injected via dependency.

    Returns:
        IntempusClient: Client configured to communicate with the Intempus API.

    Notes:
        - Cached for 60 seconds to reuse underlying configuration.
        - References the Intempus Case API:
          https://intempus.dk/web-doc/v1/#tag---Case
    """
    return IntempusClient(config)


@aiocache.cached(ttl=60)
async def get_db_client(config: Annotated[config.Config, Depends(dependency=get_config)]) -> DBClient:
    """
    Provide a cached database client.

    Args:
        config (Config): Application configuration injected via dependency.

    Returns:
        DBClient: Client for interacting with the local database.

    Notes:
        - Cached for 60 seconds to limit database engine re-creation.
        - Uses SQLite as configured in the application settings.
    """
    return DBClient(config)


def get_logger_dep(logger: logging.Logger):
    """
    Create a FastAPI dependency that provides a shared logger instance.

    Args:
        logger (logging.Logger): Logger instance to be injected into route handlers.

    Returns:
        Callable[[], logging.Logger]: Dependency function returning the logger.

    Notes:
        - Used to inject the same logger instance across all API routes.
        - Wired via FastAPI dependency overrides in the application factory.
    """

    def get_logger() -> logging.Logger:
        return logger

    return get_logger
