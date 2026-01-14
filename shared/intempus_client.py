import logging
from typing import Iterator

import httpx

from config import Config
from shared import dto, error


class IntempusClient:
    def __init__(self, config: Config) -> None:
        self.base_uri = config.intempus_api_uri
        self.case_uri = f"{self.base_uri}/case/"
        self.headers = {
            "Authorization": f"apikey {config.intempus_api_user}:{config.intempus_api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, logger: logging.Logger, **kwargs) -> httpx.Response | error.ErrorDetail:
        try:
            with httpx.Client(headers=self.headers, timeout=30) as client:
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
        offset = 0
        while True:
            response = self._request("GET", self.case_uri, logger, params={"limit": limit, "offset": offset})

            if isinstance(response, error.ErrorDetail):
                raise RuntimeError(f"API returned error: {response}")
            else:
                case_page = dto.CaseQueryResponseDTO(**response.json())
                yield case_page

                if not case_page.meta.next:
                    break

                offset += limit

    def create_case(self, case: dto.CaseCreateDTO, logger: logging.Logger) -> dto.CaseResponseDTO | error.ErrorDetail:
        response = self._request("POST", self.case_uri, logger, json=case.model_dump())
        if isinstance(response, error.ErrorDetail):
            return response
        else:
            return dto.CaseResponseDTO(**response.json())

    def update_case(
        self, id: int, case: dto.CaseUpdateDTO, logger: logging.Logger
    ) -> dto.CaseResponseDTO | error.ErrorDetail:
        response = self._request("PUT", f"{self.case_uri}{id}/", logger, json=case.model_dump(exclude_none=True))
        if isinstance(response, error.ErrorDetail):
            return response
        else:
            return dto.CaseResponseDTO(**response.json())

    def delete_case(self, case_id: int, logger: logging.Logger) -> None | error.ErrorDetail:
        response = self._request("DELETE", f"{self.case_uri}{case_id}/", logger)
        if isinstance(response, error.ErrorDetail):
            return response

        return None
