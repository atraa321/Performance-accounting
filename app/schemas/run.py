from typing import List

from pydantic import BaseModel


class RunCreate(BaseModel):
    month: str
    dept_name: str
    rule_version: str


class RunResponse(BaseModel):
    run_id: int
    month: str
    dept_name: str
    rule_version: str


class SummaryRow(BaseModel):
    name: str
    role: str
    direct_total: float
    pool_nursing: float
    pool_doctor: float
    surplus: float
    grand_total: float


class SummaryResponse(BaseModel):
    rows: List[SummaryRow]


class ManualEntry(BaseModel):
    name: str
    amount: float


class ManualEntryPayload(BaseModel):
    rows: List[ManualEntry]


class ManualEntryV2(BaseModel):
    target_type: str
    target_value: str
    item_type: str
    amount: float


class ManualEntryPayloadV2(BaseModel):
    rows: List[ManualEntryV2]
