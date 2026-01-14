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
    try:
        return Config()  # ty:ignore[missing-argument]
    except Exception:
        logger.error("Failed to load configuration", exc_info=True)

    return None


def main(config: Config, logger: logging.Logger) -> None:
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
