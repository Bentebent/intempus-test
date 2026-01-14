from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel


class Meta(BaseModel):
    limit: int
    next: Optional[str]
    offset: Optional[int]
    previous: Optional[str]
    total_count: int


class CaseResponseDTO(BaseModel):
    id: int

    responsible: Optional[str] = None
    co_responsible: Optional[str] = None
    case_state: Optional[str] = None
    customer: Optional[str] = None
    case_group: Optional[str] = None
    case_group_full: Optional[Dict] = None
    department: Optional[str] = None
    parent: Optional[str] = None
    priority: Optional[str] = None
    responsibles: Optional[list[str]] = None

    customer_country: Optional[str] = None
    customer_city: Optional[str] = None
    customer_street_address: Optional[str] = None
    customer_zip_code: Optional[str] = None
    customer_latitude: Optional[float] = None
    customer_longitude: Optional[float] = None
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None

    department_name: Optional[str] = None
    department_id: Optional[str] = None
    responsible_name: Optional[str] = None
    responsible_id: Optional[str] = None
    co_responsible_name: Optional[str] = None
    co_responsible_id: Optional[str] = None
    case_state_name: Optional[str] = None
    case_state_id: Optional[str] = None

    parent_name: Optional[str] = None
    root_parent: Optional[str] = None
    number_of_children: Optional[int] = None

    creation_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    street_address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    number: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    hour_budget: Optional[float] = None

    remarks_required: Optional[bool] = None
    file_upload_required: Optional[bool] = None
    active: Optional[bool] = None
    permit_new_workreports: Optional[bool] = None
    all_employees_may_add_work_reports: Optional[bool] = None
    all_worktypes_may_used_in_work_reports: Optional[bool] = None
    geofence: Optional[bool] = None

    resource_uri: Optional[str] = None
    logical_timestamp: Optional[int] = None
    creation_id: Optional[str] = None
    uuid: Optional[str] = None


class CaseQueryResponseDTO(BaseModel):
    meta: Meta
    objects: list[CaseResponseDTO]


class CaseBaseDTO(BaseModel):
    responsible: Optional[str] = None
    co_responsible: Optional[str] = None
    case_state: Optional[str] = None
    customer: Optional[str] = None
    case_group: Optional[str] = None
    department: Optional[str] = None
    parent: Optional[str] = None
    priority: Optional[str] = None

    customer_country: Optional[str] = None
    customer_city: Optional[str] = None
    customer_street_address: Optional[str] = None
    customer_zip_code: Optional[str] = None
    customer_latitude: Optional[float] = None
    customer_longitude: Optional[float] = None
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None

    department_name: Optional[str] = None
    department_id: Optional[str] = None
    responsible_name: Optional[str] = None
    responsible_id: Optional[str] = None
    co_responsible_name: Optional[str] = None
    co_responsible_id: Optional[str] = None
    case_state_name: Optional[str] = None
    case_state_id: Optional[str] = None

    parent_name: Optional[str] = None
    root_parent: Optional[str] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    number: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    hour_budget: Optional[float] = None

    street_address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    remarks_required: Optional[bool] = None
    file_upload_required: Optional[bool] = None
    active: Optional[bool] = None
    permit_new_workreports: Optional[bool] = None
    all_employees_may_add_work_reports: Optional[bool] = None
    all_worktypes_may_used_in_work_reports: Optional[bool] = None
    geofence: Optional[bool] = None
    creation_id: Optional[str] = None

    model_config = {"extra": "forbid"}


class CaseCreateDTO(CaseBaseDTO):
    customer: str
    number: str
    name: str


class CaseUpdateDTO(CaseBaseDTO):
    pass
