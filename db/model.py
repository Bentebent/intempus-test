from typing import Optional

from sqlmodel import Field, SQLModel


class Case(SQLModel, table=True):
    __tablename__ = "cases"

    id: Optional[int] = Field(default=0, primary_key=True)
    logical_timestamp: int
    blob: str
