import logging
import threading

from db import db_client
from shared import intempus_client


class IntempusSynchronizer(threading.Thread):
    def __init__(
        self, intempus_client: intempus_client.IntempusClient, db_client: db_client.DBClient, logger: logging.Logger
    ) -> None:
        self._ticker = threading.Event()
        self._intempus_client = intempus_client
        self._db_client = db_client
        self._logger = logger

        super().__init__()
        self.start()

    def run(self):
        while not self._ticker.wait(5):
            self._synchronize_cases()

    def _synchronize_cases(self) -> None:
        self._logger.info("Fetching cases from Intempus")
        try:
            self._db_client.synchronize_with_intempus(self._intempus_client.get_cases(self._logger, limit=1000))
        except Exception:
            self._logger.error("Failed to synchronize with Intempus", exc_info=True)
