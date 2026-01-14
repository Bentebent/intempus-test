import logging
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine, select

import config
from db.model import Case
from shared.dto import CaseQueryResponseDTO


class DBClient:
    """
    Client for interacting with the local database to persist Intempus case data.

    This client provides methods to insert, update, delete, and synchronize
    case data received from the Intempus API. Cases are stored in a SQLite
    database as JSON blobs with a logical timestamp for versioning.

    Attributes:
        _engine: SQLModel engine connected to the SQLite database specified
            in the configuration.

    Notes:
        - Case data structure corresponds to the Intempus Case API model:
          https://intempus.dk/web-doc/v1/#tag---Case
        - Uses SQLModel/SQLAlchemy for database access.
    """

    def __init__(self, config: config.Config):
        self._engine = create_engine(f"sqlite:///{config.db_name}")
        SQLModel.metadata.create_all(self._engine)

    def insert_case(self, case: Case) -> None:
        """
        Insert a new case into the local database.

        Args:
            case (Case): The Case object to insert.

        Notes:
            - Commits the session immediately.
        """
        with Session(self._engine) as session:
            session.add(case)
            session.commit()

    def update_case(self, case: Case, logger: logging.Logger) -> None:
        """
        Update an existing case in the local database if it exists.

        Args:
            case (Case): The Case object containing updated data.
            logger (logging.Logger): Logger for info and error messages.

        Notes:
            - Only updates the logical_timestamp and blob fields.
            - If the case does not exist locally, nothing happens.
        """
        logger.info(f"Attempting to update case {case.id}")
        with Session(bind=self._engine) as session:
            local_case = session.get(Case, case.id)
            logger.info(f"Found local case {local_case}")
            if local_case:
                local_case.logical_timestamp = case.logical_timestamp
                local_case.blob = case.blob
                session.commit()

    def delete_case(self, id: int) -> bool:
        """
        Delete a case from the local database by ID.

        Args:
            id (int): The ID of the case to delete.

        Returns:
            bool: True if the case existed and was deleted, False otherwise.
        """
        with Session(self._engine) as session:
            case_to_delete = session.get(Case, id)
            if case_to_delete:
                session.delete(case_to_delete)
                session.commit()
                return True

            return False

    def synchronize_with_intempus(self, intempus_cases: Iterator[CaseQueryResponseDTO]) -> None:
        """
        Synchronize local database cases with data from Intempus.

        This method performs a full comparison between local cases and
        remote cases retrieved from the Intempus API. It ensures that:

            - Remote cases not present locally are inserted.
            - Cases with a higher logical_timestamp are updated.
            - Local cases missing remotely are deleted.

        Args:
            intempus_cases (Iterator[CaseQueryResponseDTO]): Iterator over
                pages of Case objects returned from the Intempus API.

        Notes:
            - The remote Case objects are expected to follow the structure
              of `CaseResponseDTO`.
            - Commits occur after processing each page of results.
            - Uses the `logical_timestamp` field to detect changes.
            - Reference: Intempus API Case documentation
              https://intempus.dk/web-doc/v1/#tag---Case
        """
        with Session(self._engine) as session:
            min_local_id = 0
            local_case = None
            local_iter = None

            for page in intempus_cases:
                remote_iter = iter(page.objects)
                remote_case = next(remote_iter, None)

                if local_case is None and local_iter is None:
                    stmt = select(Case).where(Case.id >= min_local_id).order_by(Case.id)  # ty:ignore[unsupported-operator, invalid-argument-type]
                    local_iter = iter(session.exec(stmt))
                    local_case = next(local_iter, None)

                while remote_case is not None or local_case is not None:
                    if remote_case and local_case:
                        if remote_case.id == local_case.id:
                            if remote_case.logical_timestamp > local_case.logical_timestamp:
                                local_case.logical_timestamp = remote_case.logical_timestamp
                                local_case.blob = remote_case.model_dump_json()
                            remote_case = next(remote_iter, None)
                            local_case = next(local_iter, None)

                        elif remote_case.id < local_case.id:
                            session.add(
                                Case(
                                    id=remote_case.id,
                                    logical_timestamp=remote_case.logical_timestamp,
                                    blob=remote_case.model_dump_json(),
                                )
                            )
                            remote_case = next(remote_iter, None)

                        else:
                            session.delete(local_case)
                            local_case = next(local_iter, None)

                    elif remote_case:
                        session.add(
                            Case(
                                id=remote_case.id,
                                logical_timestamp=remote_case.logical_timestamp,
                                blob=remote_case.model_dump_json(),
                            )
                        )
                        remote_case = next(remote_iter, None)

                    elif local_case:
                        break

                if remote_case is None and page.objects:
                    max_page_id = max(obj.id for obj in page.objects)
                    min_local_id = max(min_local_id, max_page_id + 1)

                session.commit()

            if local_case is not None:
                session.delete(local_case)
                for remaining_case in local_iter:  # ty:ignore[not-iterable]
                    session.delete(remaining_case)
                session.commit()
