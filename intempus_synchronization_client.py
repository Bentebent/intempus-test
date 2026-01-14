import logging
import threading

from db import db_client
from shared import intempus_client


class IntempusSynchronizer(threading.Thread):
    """
    A background thread that periodically synchronizes case data from Intempus
    into the local database.

    This thread fetches cases from the Intempus API at regular intervals (every 5 seconds)
    and updates the local database using the provided DB client. Any errors during
    synchronization are logged.

    Attributes:
        _ticker (threading.Event): Event used to control the thread's sleep/wait cycles.
        _intempus_client (IntempusClient): Client for interacting with the Intempus API.
        _db_client (DBClient): Client for interacting with the local database.
        _logger (logging.Logger): Logger for info and error messages.
    """

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
        """
        Fetches cases from Intempus and synchronizes them with the local database.

        This method logs the start of synchronization, calls the Intempus client
        to retrieve cases (with a limit of 1000), and updates the database. Any
        exceptions raised during this process are caught and logged as errors.
        """
        self._logger.info("Fetching cases from Intempus")
        try:
            self._db_client.synchronize_with_intempus(self._intempus_client.get_cases(self._logger, limit=1000))
        except Exception:
            self._logger.error("Failed to synchronize with Intempus", exc_info=True)
