from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Boolean,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class RunBatch(Base):
    __tablename__ = "run_batch"

    id = Column(Integer, primary_key=True)
    month = Column(String(20), nullable=False)
    dept_name = Column(String(100), nullable=False)
    rule_version = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    locked_at = Column(DateTime, nullable=True)


class RuleSet(Base):
    __tablename__ = "rule_set"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


class RuleParam(Base):
    __tablename__ = "rule_param"

    id = Column(Integer, primary_key=True)
    rule_set_id = Column(Integer, ForeignKey("rule_set.id"), nullable=False)
    param_key = Column(String(100), nullable=False)
    param_value = Column(String(100), nullable=False)
    param_value_num = Column(Numeric(12, 4), nullable=True)
    param_desc = Column(String(200), nullable=True)


class DictItemMapping(Base):
    __tablename__ = "dict_item_mapping"

    id = Column(Integer, primary_key=True)
    raw_item_name = Column(String(200), nullable=False)
    item_code = Column(String(50), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)


class DictItemBehavior(Base):
    __tablename__ = "dict_item_behavior"

    id = Column(Integer, primary_key=True)
    item_code = Column(String(50), unique=True, nullable=False)
    behavior_type = Column(String(30), nullable=False)


class RawHospitalPerfItem(Base):
    __tablename__ = "raw_hospital_perf_item"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    item_name = Column(String(200), nullable=False)
    item_name_norm = Column(String(200), nullable=False)
    period_tag = Column(String(20), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawRoster(Base):
    __tablename__ = "raw_roster"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    perf_score = Column(Numeric(12, 2), nullable=False)
    eligible_for_surplus_weight = Column(Boolean, nullable=True)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawNightShift(Base):
    __tablename__ = "raw_night_shift"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    night_count = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawReadingFee(Base):
    __tablename__ = "raw_reading_fee"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    category = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawDoctorWorkload(Base):
    __tablename__ = "raw_doctor_workload"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    workload = Column(Numeric(12, 2), nullable=False)
    bed_days = Column(Numeric(12, 2), nullable=False)
    admission_cert_count = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawNurseWorkload(Base):
    __tablename__ = "raw_nurse_workload"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    score = Column(Numeric(12, 2), nullable=False)
    blood_draw_count = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawManualDoctorWorkloadPay(Base):
    __tablename__ = "raw_manual_doctor_workload_pay"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawManualPoolAdjust(Base):
    __tablename__ = "raw_manual_pool_adjust"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    pool_code = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    note = Column(String(200), nullable=True)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawManualStudyLeavePay(Base):
    __tablename__ = "raw_manual_study_leave_pay"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    row_no = Column(Integer, nullable=True)
    sheet_name = Column(String(100), nullable=True)


class RawManualEntry(Base):
    __tablename__ = "raw_manual_entry"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_value = Column(String(100), nullable=False)
    item_type = Column(String(30), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)


class DimEmployeeMonth(Base):
    __tablename__ = "dim_employee_month"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    role_type = Column(String(30), nullable=False)
    perf_score = Column(Numeric(12, 2), nullable=False)
    is_director = Column(Boolean, nullable=False, default=False)
    is_deputy_director = Column(Boolean, nullable=False, default=False)
    is_head_nurse = Column(Boolean, nullable=False, default=False)
    eligible_for_surplus_weight = Column(Boolean, nullable=False, default=True)
    is_external = Column(Boolean, nullable=False, default=False)


class FactPool(Base):
    __tablename__ = "fact_pool"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    pool_code = Column(String(50), nullable=False)
    source_item_code = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    note = Column(String(200), nullable=True)


class FactPoolAlloc(Base):
    __tablename__ = "fact_pool_alloc"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    pool_code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    weight = Column(Numeric(12, 4), nullable=False)
    note = Column(String(200), nullable=True)


class FactPayDetail(Base):
    __tablename__ = "fact_pay_detail"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(200), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    source_item_code = Column(String(50), nullable=True)
    pay_type = Column(String(30), nullable=False)
    pool_code = Column(String(50), nullable=True)
    calc_note = Column(String(200), nullable=True)


class FactPaySummary(Base):
    __tablename__ = "fact_pay_summary"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    direct_total = Column(Numeric(12, 2), nullable=False)
    pool_nursing = Column(Numeric(12, 2), nullable=False)
    pool_doctor = Column(Numeric(12, 2), nullable=False)
    surplus = Column(Numeric(12, 2), nullable=False)
    grand_total = Column(Numeric(12, 2), nullable=False)


class ReconcileItem(Base):
    __tablename__ = "reconcile_item"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    item_code = Column(String(50), nullable=False)
    source_amount = Column(Numeric(12, 2), nullable=False)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    delta = Column(Numeric(12, 2), nullable=False)
    note = Column(String(200), nullable=True)


class QcIssue(Base):
    __tablename__ = "qc_issue"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("run_batch.id"), nullable=False)
    issue_type = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False, default="WARN")
    payload = Column(JSON, nullable=True)
    sheet_name = Column(String(100), nullable=True)
    row_no = Column(Integer, nullable=True)
