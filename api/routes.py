import logging

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from api.deps import get_db_client, get_intempus_client
from db import model
from db.db_client import DBClient
from shared import dto, error
from shared.intempus_client import IntempusClient


def get_logger() -> logging.Logger:
    raise RuntimeError("Dependency not wired!")


router = APIRouter(prefix="/case")


def raise_http_exception_from_error(status_code: int, error: error.ErrorDetail) -> None:
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
    app.include_router(router)
