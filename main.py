from config import Config
import dotenv
import logging
import sys
from typing import Optional



def _get_config(logger: logging.Logger) -> Optional[Config]:
    try:
        return Config()  # ty:ignore[missing-argument]
    except Exception:
        logger.error("Failed to load configuration", exc_info=True)
        
    return None


def main():
    print("Hello from intempus-sync!")


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

    main()
