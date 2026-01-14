"""
API routes for managing Case resources.

This module provides endpoints to create, update, and delete Case objects
in the Intempus system, while synchronizing changes with the local database.

Endpoints:
    - POST /case: Create a new case in Intempus and the local database.
    - PUT /case/{id}: Update an existing case in Intempus and the local database.
    - DELETE /case/{id}: Delete a case from Intempus and the local database.

Dependencies:
    - IntempusClient: Client for communicating with the Intempus API.
      Docs: https://intempus.dk/web-doc/v1/#tag---Case
    - DBClient: Client for local database operations.
    - Logger: Standard Python logger for audit and debug messages.

Notes:
    - All error responses from Intempus are converted to HTTPException responses
      with the original status code and error details.
    - The local database is updated only if the Intempus operation succeeds,
      except in the case of 404 on delete, where the local record is cleaned up.
"""

import logging

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from api.deps import get_db_client, get_intempus_client
from db import model
from db.db_client import DBClient
from shared import dto, error
from shared.intempus_client import IntempusClient


def get_logger() -> logging.Logger:
    """
    Dependency placeholder for retrieving a logger instance.

    Raises:
        RuntimeError: If the dependency is not properly wired in FastAPI.

    Notes:
        - In production, this should be replaced by a proper dependency that
          returns a configured Logger instance.
    """
    raise RuntimeError("Dependency not wired!")


router = APIRouter(prefix="/case")


def raise_http_exception_from_error(status_code: int, error: error.ErrorDetail) -> None:
    """
    Convert an Intempus ErrorDetail into a FastAPI HTTPException.

    Args:
        status_code (int): HTTP status code to return.
        error (ErrorDetail): The error detail object returned by Intempus.

    Raises:
        HTTPException: With structured detail including title, version, and messages.

    Notes:
        - Preserves the error messages returned by the Intempus API.
    """
    messages = [item.message for item in error.error_messages]
    detail = {
        "title": error.title,
        "detail": error.detail,
        "version": error.version,
        "error_messages": messages,
    }

    raise HTTPException(status_code=status_code, detail=detail)


@router.post("", status_code=201)
async def create(
    case: dto.CaseCreateDTO,
    intempus_client: IntempusClient = Depends(get_intempus_client),
    db_client: DBClient = Depends(dependency=get_db_client),
    logger: logging.Logger = Depends(get_logger),
):
    """
    Create a new Case in Intempus and the local database.

    Args:
        case (CaseCreateDTO): Data transfer object containing case details.
        intempus_client (IntempusClient): Client for interacting with Intempus.
        db_client (DBClient): Client for local database operations.
        logger (Logger): Logger for audit/debug messages.

    Returns:
        CaseResponseDTO: The newly created case as returned by Intempus.

    Raises:
        HTTPException: If the Intempus API returns an error.
    """
    logger.info(f"Creating case {case.number}")
    response = intempus_client.create_case(case, logger)
    if isinstance(response, error.ErrorDetail):
        raise_http_exception_from_error(response.status_code, response)
    else:
        db_client.insert_case(
            model.Case(id=response.id, logical_timestamp=response.logical_timestamp, blob=response.model_dump_json())
        )

    return response


@router.put("/{id}", status_code=201)
async def update(
    id: int,
    case: dto.CaseUpdateDTO,
    intempus_client: IntempusClient = Depends(get_intempus_client),
    db_client: DBClient = Depends(dependency=get_db_client),
    logger: logging.Logger = Depends(get_logger),
):
    """
    Update an existing Case in Intempus and the local database.

    Args:
        id (int): The ID of the case to update.
        case (CaseUpdateDTO): Data transfer object containing updated fields.
        intempus_client (IntempusClient): Client for interacting with Intempus.
        db_client (DBClient): Client for local database operations.
        logger (Logger): Logger for audit/debug messages.

    Returns:
        CaseResponseDTO: The updated case as returned by Intempus.

    Raises:
        HTTPException: If the Intempus API returns an error.
    """
    logger.info(f"Updating case {id}")
    response = intempus_client.update_case(id, case, logger)
    if isinstance(response, error.ErrorDetail):
        raise_http_exception_from_error(response.status_code, response)
    else:
        db_client.update_case(
            model.Case(id=response.id, logical_timestamp=response.logical_timestamp, blob=response.model_dump_json()),
            logger,
        )

    return response


@router.delete(path="/{id}", status_code=204)
async def delete(
    id: int,
    intempus_client: IntempusClient = Depends(get_intempus_client),
    db_client: DBClient = Depends(dependency=get_db_client),
    logger: logging.Logger = Depends(dependency=get_logger),
):
    """
    Delete a Case from Intempus and the local database.

    Args:
        id (int): The ID of the case to delete.
        intempus_client (IntempusClient): Client for interacting with Intempus.
        db_client (DBClient): Client for local database operations.
        logger (Logger): Logger for audit/debug messages.

    Raises:
        HTTPException: If the Intempus API returns an error other than 404.

    Notes:
        - If Intempus returns 404, the local record is deleted anyway to
          maintain consistency.
    """
    logger.info(f"Deleting case {id}")
    response = intempus_client.delete_case(id, logger)

    if isinstance(response, error.ErrorDetail):
        # Someone might have already deleted the case in Intempus, this is expressed as a 404
        if response.status_code == 404:
            db_client.delete_case(id)
        else:
            raise_http_exception_from_error(response.status_code, response)
    else:
        db_client.delete_case(id)

    logger.info(f"Deleted case {id}")


def append_routes(app: FastAPI) -> None:
    """
    Attach the Case router to a FastAPI application.

    Args:
        app (FastAPI): The FastAPI app instance to attach routes to.
    """
    app.include_router(router)
