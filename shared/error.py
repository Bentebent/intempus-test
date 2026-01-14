from pydantic import BaseModel


class ErrorMessageItem(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    title: str
    status_code: int
    detail: str
    version: str
    error_messages: list[ErrorMessageItem]
