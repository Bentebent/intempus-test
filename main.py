"""
Entry point for the Intempus synchronization service.

This script initializes the FastAPI app, sets up logging, loads configuration
from environment variables, and starts a background thread to synchronize
cases from Intempus into the local database.

It also starts the Uvicorn server to expose the API.

Key Components:
    - IntempusClient: Client for interacting with the Intempus REST API.
      API docs: https://intempus.dk/web-doc/v1/#tag---Case
    - DBClient: Local database client for persisting case data.
    - IntempusSynchronizer: Background thread that periodically fetches
      cases from Intempus and updates the database.
    - FastAPI app: Exposes endpoints for API access.
    - Uvicorn: ASGI server for serving the FastAPI app.

Usage:
    python main.py
"""

import logging
import sys
from typing import Optional

import dotenv
import uvicorn

from api.main import create_api
from config import Config
from db.db_client import DBClient
from intempus_synchronization_client import IntempusSynchronizer
from shared.intempus_client import IntempusClient

intempus_synchronization_client: IntempusSynchronizer | None = None


def _get_config(logger: logging.Logger) -> Optional[Config]:
    """
    Load configuration from environment variables.

    This function reads environment variables and constructs a Config object
    containing settings for the API, database, and Intempus client.

    Args:
        logger (logging.Logger): Logger used to report errors during config loading.

    Returns:
        Optional[Config]: A Config object if successfully loaded, otherwise None.

    Notes:
        - Configuration must include Intempus API credentials for the synchronizer
          to function correctly.
        - Errors are logged; the caller should handle a None return value.
    """
    try:
        return Config()  # ty:ignore[missing-argument]
    except Exception:
        logger.error("Failed to load configuration", exc_info=True)

    return None


def main(config: Config, logger: logging.Logger) -> None:
    """
    Start the Intempus synchronization API service.

    Initializes the FastAPI app, starts a background thread for synchronizing
    cases from Intempus into the local database, and runs the Uvicorn server.

    Args:
        config (Config): Configuration object containing API, database, and Intempus settings.
        logger (logging.Logger): Logger for reporting runtime events and errors.

    Notes:
        - The IntempusSynchronizer will run in a background thread and periodically
          fetch cases from the Intempus API.
        - Ensure that Intempus API credentials are valid.
        - FastAPI endpoints are available once the server starts at host 0.0.0.0
          and the port specified in the configuration.

    See also:
        - Intempus API documentation (Case endpoints):
          https://intempus.dk/web-doc/v1/#tag---Case
    """
    app = create_api(logger)

    global intempus_synchronization_client
    intempus_synchronization_client = IntempusSynchronizer(IntempusClient(config), DBClient(config), logger)

    uvicorn.run(app, host="0.0.0.0", port=config.api_port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("intempus_sync")
    logger.info("Initializing Intempus sync API")

    if not dotenv.load_dotenv(r".\.dev\.env.dev"):
        logging.debug("No environment variables read from env var file")

    config = _get_config(logger)
    if not config:
        logger.error("Configuration incomplete or missing, exiting")
        sys.exit(1)
    else:
        main(config, logger)
