import logging
import sys
from typing import Optional

import dotenv
import uvicorn

from api.main import create_api
from config import Config


def _get_config(logger: logging.Logger) -> Optional[Config]:
    try:
        return Config()  # ty:ignore[missing-argument]
    except Exception:
        logger.error("Failed to load configuration", exc_info=True)

    return None


def foo(config: Config, logger: logging.Logger) -> None:
    app = create_api(config, logger)
    print("Hello from intempus-sync!")

    uvicorn.run(
        app, host="0.0.0.0", port=config.api_port
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("intempus_sync")
    logger.info("Initializing Intempus sync API")

    if not dotenv.load_dotenv(r".\.dev\.env.dev"):
        logging.debug("No environment variables read from env var file")

    config = _get_config(logger)
    if not config:
        logger.error("Configuration incomplete or missing, exiting")
        sys.exit(1)
    else:
        foo(config, logger)
