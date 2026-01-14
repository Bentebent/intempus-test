import logging
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine, select

import config
from db.model import Case
from shared.dto import CaseQueryResponseDTO


class DBClient:
    def __init__(self, config: config.Config):
        self._engine = create_engine(f"sqlite:///{config.db_name}")
        SQLModel.metadata.create_all(self._engine)

    def insert_case(self, case: Case) -> None:
        with Session(self._engine) as session:
            session.add(case)
            session.commit()

    def update_case(self, case: Case, logger: logging.Logger) -> None:
        logger.info(f"Attempting to update case {case.id}")
        with Session(bind=self._engine) as session:
            local_case = session.get(Case, case.id)
            logger.info(f"Found local case {local_case}")
            if local_case:
                local_case.logical_timestamp = case.logical_timestamp
                local_case.blob = case.blob
                session.commit()

    def delete_case(self, id: int) -> bool:
        with Session(self._engine) as session:
            case_to_delete = session.get(Case, id)
            if case_to_delete:
                session.delete(case_to_delete)
                session.commit()
                return True

            return False

    def synchronize_with_intempus(self, intempus_cases: Iterator[CaseQueryResponseDTO]) -> None:
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
