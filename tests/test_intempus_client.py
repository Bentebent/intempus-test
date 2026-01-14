import logging
from unittest.mock import patch

import pytest

from shared import dto, error
from shared.intempus_client import IntempusClient


@pytest.fixture
def client(get_config):
    return IntempusClient(get_config)


def test_create_case_http_error(client):
    case_dto = dto.CaseCreateDTO(customer="Acme", number="123", name="Test Case")

    error_detail = error.ErrorDetail(
        title="Unauthorized",
        status_code=401,
        detail="API key invalid",
        version="1.0.0",
        error_messages=[error.ErrorMessageItem(message="Invalid key")],
    )

    with patch.object(client, "_request", return_value=error_detail):
        response = client.create_case(case_dto, logging.getLogger())
        assert isinstance(response, error.ErrorDetail)
        assert response.status_code == 401
