import logging
from typing import Iterator

import httpx

from config import Config
from shared import dto, error


class IntempusClient:
    """
    Client for interacting with the Intempus API to manage case data.

    This client supports fetching, creating, updating, and deleting cases,
    with built-in error handling and logging for HTTP and network issues.

    Attributes:
        _base_uri (str): Base URL of the Intempus API.
        _case_uri (str): URL endpoint for case-related operations.
        _headers (dict): HTTP headers including authorization and content type.
    """

    def __init__(self, config: Config) -> None:
        self._base_uri = config.intempus_api_uri
        self._case_uri = f"{self._base_uri}/case/"
        self._headers = {
            "Authorization": f"apikey {config.intempus_api_user}:{config.intempus_api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, logger: logging.Logger, **kwargs) -> httpx.Response | error.ErrorDetail:
        """
        Perform an HTTP request to the Intempus API with error handling.

        Args:
            method (str): HTTP method, e.g., "GET", "POST", "PUT", "DELETE".
            url (str): Full URL of the endpoint.
            logger (logging.Logger): Logger instance for logging errors.
            **kwargs: Additional arguments to pass to httpx.Client.request.

        Returns:
            httpx.Response | error.ErrorDetail: The response object on success,
            or an ErrorDetail object if the request failed.

        Logs:
            Any HTTP or network errors encountered during the request.
        """
        try:
            with httpx.Client(headers=self._headers, timeout=30) as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            text = exc.response.text
            logger.error(f"HTTP error {status}: {text}")

            if status == 400:
                title = "Bad Request"
            elif status == 401:
                title = "Unauthorized"
            elif status == 403:
                title = "Forbidden"
            elif status == 404:
                title = "Not Found"
            else:
                title = f"HTTP {status}"

            return error.ErrorDetail(
                title=title,
                status_code=status,
                detail=f"Upstream API returned status {status}",
                version="1.0.0",
                error_messages=[error.ErrorMessageItem(message=text)],
            )

        except httpx.RequestError as exc:
            logger.error(f"Network error: {exc}")
            return error.ErrorDetail(
                title="Network Error",
                status_code=503,
                detail=str(exc),
                version="1.0.0",
                error_messages=[error.ErrorMessageItem(message="Could not reach upstream API")],
            )

    def get_cases(self, logger: logging.Logger, limit=1000) -> Iterator["dto.CaseQueryResponseDTO"]:
        """
        Fetch cases from Intempus in a paginated manner.

        Args:
            logger (logging.Logger): Logger instance for logging.
            limit (int, optional): Maximum number of cases per request. Defaults to 1000.

        Yields:
            Iterator[dto.CaseQueryResponseDTO]: Each page of case results as a DTO.

        Raises:
            RuntimeError: If the API returns an error response.
        """
        offset = 0
        while True:
            response = self._request("GET", self._case_uri, logger, params={"limit": limit, "offset": offset})

            if isinstance(response, error.ErrorDetail):
                raise RuntimeError(f"API returned error: {response}")
            else:
                case_page = dto.CaseQueryResponseDTO(**response.json())
                yield case_page

                if not case_page.meta.next:
                    break

                offset += limit

    def create_case(self, case: dto.CaseCreateDTO, logger: logging.Logger) -> dto.CaseResponseDTO | error.ErrorDetail:
        """
        Create a new case in Intempus.

        Args:
            case (dto.CaseCreateDTO): Data transfer object representing the new case.
            logger (logging.Logger): Logger instance for logging.

        Returns:
            dto.CaseResponseDTO | error.ErrorDetail: The created case DTO if successful,
            otherwise an ErrorDetail object describing the failure.
        """
        response = self._request("POST", self._case_uri, logger, json=case.model_dump())
        if isinstance(response, error.ErrorDetail):
            return response
        else:
            return dto.CaseResponseDTO(**response.json())

    def update_case(
        self, id: int, case: dto.CaseUpdateDTO, logger: logging.Logger
    ) -> dto.CaseResponseDTO | error.ErrorDetail:
        """
        Update an existing case in Intempus.

        Args:
            id (int): ID of the case to update.
            case (dto.CaseUpdateDTO): DTO containing fields to update.
            logger (logging.Logger): Logger instance for logging.

        Returns:
            dto.CaseResponseDTO | error.ErrorDetail: Updated case DTO on success,
            or ErrorDetail object if the update fails.
        """
        response = self._request("PUT", f"{self._case_uri}{id}/", logger, json=case.model_dump(exclude_none=True))
        if isinstance(response, error.ErrorDetail):
            return response
        else:
            return dto.CaseResponseDTO(**response.json())

    def delete_case(self, case_id: int, logger: logging.Logger) -> None | error.ErrorDetail:
        """
        Delete a case from Intempus.

        Args:
            case_id (int): ID of the case to delete.
            logger (logging.Logger): Logger instance for logging.

        Returns:
            None | error.ErrorDetail: None if deletion is successful,
            otherwise an ErrorDetail object describing the failure.
        """
        response = self._request("DELETE", f"{self._case_uri}{case_id}/", logger)
        if isinstance(response, error.ErrorDetail):
            return response

        return None
