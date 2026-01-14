from pydantic import BaseModel


class ErrorMessageItem(BaseModel):
    """
    Represents a single error message item.

    Attributes:
        message (str): Human-readable description of the error.
    """

    message: str


class ErrorDetail(BaseModel):
    """
    Represents a detailed error response from the API.

    Attributes:
        title (str): Short, descriptive title of the error (e.g., "Bad Request").
        status_code (int): HTTP status code associated with the error.
        detail (str): Detailed description of the error.
        version (str): Version of the error format or API.
        error_messages (list[ErrorMessageItem]): List of individual error messages providing more context.
    """

    title: str
    status_code: int
    detail: str
    version: str
    error_messages: list[ErrorMessageItem]
