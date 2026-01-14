from typing import Optional

from sqlmodel import Field, SQLModel


class Case(SQLModel, table=True):
    """
    Represents a Case record stored in the local database.

    This model is used by the DBClient to persist Intempus case data locally.
    Each record stores the case payload as a blob along with a logical timestamp
    for versioning.

    Attributes:
        id (Optional[int]): Primary key of the record in the local database.
        logical_timestamp (int): Version or timestamp used to track the latest
            state of the case for synchronization purposes.
        blob (str): JSON-serialized representation of the case data received
            from the Intempus API.

    Notes:
        - The structure of the case data in `blob` matches the Intempus Case
          API model.
        - See Intempus API documentation for Case fields:
          https://intempus.dk/web-doc/v1/#tag---Case
    """

    __tablename__ = "cases"

    id: Optional[int] = Field(default=0, primary_key=True)
    logical_timestamp: int
    blob: str
