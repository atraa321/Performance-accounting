from __future__ import annotations

from collections import defaultdict
import hashlib
from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, func, select

from app.calc.utils import (
    allocate_by_weight,
    detect_role_type,
    extract_period_tag,
    is_lab_category,
    normalize_item_name,
    role_flags,
    round_money,
    to_decimal,
)
from app.core.seed import seed_defaults
from app.models.models import (
    DictItemBehavior,
    DictItemMapping,
    DimEmployeeMonth,
    FactPayDetail,
    FactPaySummary,
    FactPool,
    FactPoolAlloc,
    QcIssue,
    RawDoctorWorkload,
    RawHospitalPerfItem,
    RawManualDoctorWorkloadPay,
    RawManualEntry,
    RawManualPoolAdjust,
    RawManualStudyLeavePay,
    RawNightShift,
    RawNurseWorkload,
    RawReadingFee,
    RawRoster,
    ReconcileItem,
    RuleParam,
)

POOL_NURSING = "NURSING_POOL"
POOL_DOCTOR = "DOCTOR_POOL"

PAY_DIRECT = "DIRECT"
PAY_POOL_NURSING = "POOL_NURSING"
PAY_POOL_DOCTOR = "POOL_DOCTOR"
PAY_SURPLUS = "SURPLUS"


class CalcError(Exception):
    pass


def _clear_run(session, run_id: int) -> None:
    for model in (FactPayDetail, FactPaySummary, FactPool, FactPoolAlloc, ReconcileItem, QcIssue, DimEmployeeMonth):
        session.execute(delete(model).where(model.run_id == run_id))
    session.flush()


def _load_rule_params(session) -> dict[str, Decimal]:
    params = {}
    for row in session.execute(select(RuleParam)).scalars():
        try:
            params[row.param_key] = Decimal(str(row.param_value))
            continue
        except Exception:
            pass
        if row.param_value_num is not None:
            params[row.param_key] = Decimal(str(row.param_value_num))
    return params


def _load_item_mapping(session) -> list[tuple[str, str, int]]:
    rows = (
        session.execute(select(DictItemMapping).where(DictItemMapping.is_active == True)).scalars().all()
    )
    mapped = [(r.raw_item_name, r.item_code, r.priority) for r in rows]
    mapped.sort(key=lambda r: r[2])
    return mapped


def _load_item_behaviors(session) -> dict[str, str]:
    rows = session.execute(select(DictItemBehavior)).scalars().all()
    return {r.item_code: r.behavior_type for r in rows}


def _map_item_code(name_norm: str, mapping: list[tuple[str, str, int]]) -> Optional[str]:
    for raw_name, item_code, _ in mapping:
        if raw_name in name_norm:
            return item_code
    return None


def _add_qc(session, run_id: int, issue_type: str, message: str, payload=None):
    session.add(
        QcIssue(
            run_id=run_id,
            issue_type=issue_type,
            message=message,
            severity="WARN",
            payload=payload,
        )
    )


def _add_pay_detail(
    session,
    run_id: int,
    name: str,
    item_code: str,
    item_name: str,
    amount: Decimal,
    source_item_code: str,
    pay_type: str,
    pool_code: Optional[str] = None,
    note: Optional[str] = None,
):
    session.add(
        FactPayDetail(
            run_id=run_id,
            name=name,
            item_code=item_code,
            item_name=item_name,
            amount=round_money(amount),
            source_item_code=source_item_code,
            pay_type=pay_type,
            pool_code=pool_code,
            calc_note=note,
        )
    )


def calculate_run(session, run_id: int) -> dict[str, list[dict[str, object]]]:
    seed_defaults(session)
    _clear_run(session, run_id)

    params = _load_rule_params(session)
    # Night shift pay now always uses "total amount / total shifts * personal shifts".
    # Keep backward compatibility with historical rule_param rows by explicitly ignoring old unit params.
    params.pop("doctor_night_unit", None)
    params.pop("nurse_night_unit", None)
    mapping = _load_item_mapping(session)
    behaviors = _load_item_behaviors(session)

    raw_items = list(
        session.execute(
            select(RawHospitalPerfItem).where(RawHospitalPerfItem.run_id == run_id)
        ).scalars()
    )

    # Map item codes
    item_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    item_name_by_code: dict[str, str] = {}
    raw_norm_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    raw_norm_to_display: dict[str, str] = {}
    raw_norm_to_code: dict[str, str] = {}
    for item in raw_items:
        item_code = _map_item_code(item.item_name_norm, mapping)
        if not item_code:
            item_code = "UNCLASSIFIED_ITEM"
            _add_qc(
                session,
                run_id,
                "ITEM_MAPPING_MISSING",
                f"Missing mapping for item: {item.item_name}",
                {"item_name": item.item_name},
            )
        item_totals[item_code] += to_decimal(item.amount)
        item_name_by_code[item_code] = item.item_name
        raw_norm = normalize_item_name(item.item_name)
        raw_norm_totals[raw_norm] += to_decimal(item.amount)
        if raw_norm not in raw_norm_to_display or len(item.item_name) > len(raw_norm_to_display[raw_norm]):
            raw_norm_to_display[raw_norm] = item.item_name
        if item_code != "UNCLASSIFIED_ITEM":
            raw_norm_to_code[raw_norm] = item_code

    # Build employees
    roster_rows = list(
        session.execute(select(RawRoster).where(RawRoster.run_id == run_id)).scalars()
    )
    roster_names = {row.name for row in roster_rows}
    employees: dict[str, DimEmployeeMonth] = {}
    for row in roster_rows:
        role_type = detect_role_type(row.role)
        is_director, is_deputy, is_head_nurse = role_flags(row.role)
        eligible = row.eligible_for_surplus_weight
        if eligible is None:
            eligible = True
        dim = DimEmployeeMonth(
            run_id=run_id,
            name=row.name,
            role=row.role,
            role_type=role_type,
            perf_score=row.perf_score,
            is_director=is_director,
            is_deputy_director=is_deputy,
            is_head_nurse=is_head_nurse,
            eligible_for_surplus_weight=eligible,
            is_external=False,
        )
        employees[row.name] = dim
        session.add(dim)

    # Pools
    pool_totals = defaultdict(lambda: Decimal("0"))

    def _add_direct_or_redirect(
        name: str,
        item_code: str,
        item_name: str,
        amount: Decimal,
        source_item_code: str,
        note: Optional[str] = None,
    ) -> None:
        if name in roster_names:
            _add_pay_detail(
                session,
                run_id,
                name,
                item_code,
                item_name,
                amount,
                source_item_code,
                PAY_DIRECT,
                note=note,
            )
            return
        if amount == 0:
            return
        pool_totals[POOL_DOCTOR] += amount
        session.add(
            FactPool(
                run_id=run_id,
                pool_code=POOL_DOCTOR,
                source_item_code=source_item_code,
                amount=round_money(amount),
                note=f"redirect non-roster: {name}",
            )
        )
        _add_qc(
            session,
            run_id,
            "NON_ROSTER_REDIRECT",
            f"Pay redirected to doctor pool for non-roster name: {name}",
            {"name": name, "item_code": item_code, "source_item_code": source_item_code},
        )

    # External doctors from reading fee
    reading_rows = list(
        session.execute(select(RawReadingFee).where(RawReadingFee.run_id == run_id)).scalars()
    )
    for row in reading_rows:
        if row.name in employees:
            continue
        dim = DimEmployeeMonth(
            run_id=run_id,
            name=row.name,
            role="医师",
            role_type="doctor",
            perf_score=Decimal("0"),
            is_director=False,
            is_deputy_director=False,
            is_head_nurse=False,
            eligible_for_surplus_weight=False,
            is_external=True,
        )
        employees[row.name] = dim
        session.add(dim)

    session.flush()

    # Workload data
    doctor_workload = {
        row.name: row
        for row in session.execute(
            select(RawDoctorWorkload).where(RawDoctorWorkload.run_id == run_id)
        ).scalars()
    }
    nurse_workload = {
        row.name: row
        for row in session.execute(
            select(RawNurseWorkload).where(RawNurseWorkload.run_id == run_id)
        ).scalars()
    }

    # Night shift counts
    night_rows = list(
        session.execute(select(RawNightShift).where(RawNightShift.run_id == run_id)).scalars()
    )
    night_counts = defaultdict(Decimal)
    for row in night_rows:
        if row.name not in employees and row.name not in doctor_workload and row.name not in nurse_workload:
            _add_qc(
                session,
                run_id,
                "UNKNOWN_EMPLOYEE",
                f"Night shift name not in roster: {row.name}",
                {"name": row.name},
            )
            continue
        night_counts[row.name] += to_decimal(row.night_count)

    def _infer_role_type(name: str) -> Optional[str]:
        emp = employees.get(name)
        if emp:
            return emp.role_type
        if name in doctor_workload:
            return "doctor"
        if name in nurse_workload:
            return "nurse"
        return None

    # Direct pay: night shifts
    doc_night_amount = item_totals.get("DOC_NIGHT_FEE", Decimal("0"))
    doctor_nights = {
        name: count
        for name, count in night_counts.items()
        if _infer_role_type(name) == "doctor"
    }
    total_doc_nights = sum(doctor_nights.values())
    if doc_night_amount and doc_night_amount != 0:
        if total_doc_nights == 0:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Doctor night total is 0")
        else:
            alloc = allocate_by_weight(doc_night_amount, doctor_nights)
            for name, amount in alloc.items():
                _add_direct_or_redirect(
                    name,
                    "DOC_NIGHT_FEE",
                    "医师夜班",
                    amount,
                    "DOC_NIGHT_FEE",
                )

    nur_night_amount = item_totals.get("NUR_NIGHT_FEE", Decimal("0"))
    nurse_nights = {
        name: count
        for name, count in night_counts.items()
        if _infer_role_type(name) == "nurse"
    }
    total_nur_nights = sum(nurse_nights.values())
    if nur_night_amount and nur_night_amount != 0:
        if total_nur_nights == 0:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Nurse night total is 0")
        else:
            alloc = allocate_by_weight(nur_night_amount, nurse_nights)
            for name, amount in alloc.items():
                _add_direct_or_redirect(
                    name,
                    "NUR_NIGHT_FEE",
                    "护理夜班",
                    amount,
                    "NUR_NIGHT_FEE",
                )

    # Reading fee (lab 70/30)
    lab_doctor_ratio = params.get("lab_doctor_ratio", Decimal("0.7"))
    lab_nurse_ratio = params.get("lab_nurse_ratio", Decimal("0.3"))
    for row in reading_rows:
        if is_lab_category(row.category):
            doctor_amount = to_decimal(row.amount) * lab_doctor_ratio
            pool_amount = to_decimal(row.amount) * lab_nurse_ratio
        else:
            doctor_amount = to_decimal(row.amount)
            pool_amount = Decimal("0")
        if doctor_amount:
            _add_direct_or_redirect(
                row.name,
                "READING_FEE",
                "判读费",
                doctor_amount,
                "READING_FEE",
            )
        if pool_amount:
            pool_totals[POOL_NURSING] += pool_amount
            session.add(
                FactPool(
                    run_id=run_id,
                    pool_code=POOL_NURSING,
                    source_item_code="READING_FEE",
                    amount=round_money(pool_amount),
                    note="lab reading fee",
                )
            )

    # Lead reading fee
    lead_amount = item_totals.get("LEAD_READING_FEE", Decimal("0"))
    if lead_amount:
        director_ratio = params.get("lead_reading_director_ratio", Decimal("0.8"))
        deputy_ratio = params.get("lead_reading_deputy_ratio", Decimal("0"))
        head_ratio = params.get("lead_reading_head_nurse_ratio", Decimal("0.2"))
        directors = [e.name for e in employees.values() if e.is_director]
        head_nurses = [e.name for e in employees.values() if e.is_head_nurse]
        if directors:
            share = (lead_amount * director_ratio) / Decimal(len(directors))
            for name in directors:
                _add_direct_or_redirect(
                    name,
                    "LEAD_READING_FEE",
                    "科主任判读费",
                    share,
                    "LEAD_READING_FEE",
                )
        if head_nurses:
            share = (lead_amount * head_ratio) / Decimal(len(head_nurses))
            for name in head_nurses:
                _add_direct_or_redirect(
                    name,
                    "LEAD_READING_FEE",
                    "科主任判读费",
                    share,
                    "LEAD_READING_FEE",
                )
        if deputy_ratio and deputy_ratio > 0:
            deputies = [e.name for e in employees.values() if e.is_deputy_director]
            if deputies:
                share = (lead_amount * deputy_ratio) / Decimal(len(deputies))
                for name in deputies:
                    _add_direct_or_redirect(
                        name,
                        "LEAD_READING_FEE",
                        "科主任判读费",
                        share,
                        "LEAD_READING_FEE",
                    )

    # Bed subsidy
    bed_amount = item_totals.get("BED_SUBSIDY", Decimal("0"))
    if bed_amount:
        nurse_ratio = params.get("bed_subsidy_nurse_ratio", Decimal("0.3"))
        nurse_pool_amount = bed_amount * nurse_ratio
        doctor_amount = bed_amount - nurse_pool_amount
        if nurse_pool_amount:
            pool_totals[POOL_NURSING] += nurse_pool_amount
            session.add(
                FactPool(
                    run_id=run_id,
                    pool_code=POOL_NURSING,
                    source_item_code="BED_SUBSIDY",
                    amount=round_money(nurse_pool_amount),
                    note="bed subsidy nursing",
                )
            )
        doctor_weights = {
            name: to_decimal(row.bed_days)
            for name, row in doctor_workload.items()
            if name in employees and employees[name].role_type == "doctor"
        }
        total_bed_days = sum(doctor_weights.values())
        if total_bed_days == 0:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Doctor bed days total is 0")
        else:
            alloc = allocate_by_weight(doctor_amount, doctor_weights)
            for name, amount in alloc.items():
                _add_direct_or_redirect(
                    name,
                    "BED_SUBSIDY",
                    "床补",
                    amount,
                    "BED_SUBSIDY",
                )

    # Nursing pool items
    for code, name in ("NUR_SUBSIDY", "护补"), ("TCM_NURSING", "中医特色护理"), ("CHECKUP_CENTER_ALLOC", "体检中心分配"):
        amount = item_totals.get(code, Decimal("0"))
        if amount:
            pool_totals[POOL_NURSING] += amount
            session.add(
                FactPool(
                    run_id=run_id,
                    pool_code=POOL_NURSING,
                    source_item_code=code,
                    amount=round_money(amount),
                    note="nursing pool",
                )
            )

    # Doctor pool items
    for code, name in (("INSULIN_PUMP", "胰岛素泵"),):
        amount = item_totals.get(code, Decimal("0"))
        if amount:
            pool_totals[POOL_DOCTOR] += amount
            session.add(
                FactPool(
                    run_id=run_id,
                    pool_code=POOL_DOCTOR,
                    source_item_code=code,
                    amount=round_money(amount),
                    note="doctor pool",
                )
            )

    # Manual entries (new)
    manual_entry_rows = list(
        session.execute(
            select(RawManualEntry).where(RawManualEntry.run_id == run_id)
        ).scalars()
    )
    manual_item_map = {
        "WORKLOAD": ("WORKLOAD_MANUAL_PAY", "工作量"),
        "STUDY_LEAVE": ("STUDY_LEAVE_SUBSIDY", "进修产假补贴"),
        "OTHER": ("MANUAL_OTHER_PAY", "其他"),
    }
    manual_item_codes: set[str] = set()
    manual_item_overrides: set[str] = set()
    manual_raw_name_by_code: dict[str, str] = {}
    manual_raw_norms: set[str] = set()

    def _raw_item_code(name_norm: str) -> str:
        digest = hashlib.md5(name_norm.encode("utf-8")).hexdigest()[:10]
        return f"RAW_ITEM_{digest}"
    for row in manual_entry_rows:
        amount = to_decimal(row.amount)
        if amount == 0:
            continue
        raw_item_type = str(row.item_type or "").strip()
        item = manual_item_map.get(raw_item_type.upper())
        if item:
            item_code, item_name = item
            manual_item_codes.add(item_code)
            manual_item_overrides.add(item_code)
        else:
            if not raw_item_type:
                _add_qc(
                    session,
                    run_id,
                    "MANUAL_ENTRY_INVALID",
                    "Manual entry item name is empty",
                    {"item_type": row.item_type},
                )
                continue
            item_name = raw_item_type
            name_norm = normalize_item_name(item_name)
            # Prefer mapping table so manual entries like "工作量（手工）" still map to WORKLOAD_MANUAL_PAY,
            # instead of being treated as a separate RAW_ITEM_* (which can show up as duplicated rows in reconcile).
            mapped_code = _map_item_code(name_norm, mapping) or raw_norm_to_code.get(name_norm)
            if mapped_code:
                item_code = mapped_code
                item_name = raw_norm_to_display.get(name_norm, item_name)
                manual_item_codes.add(item_code)
                if item_code in ("WORKLOAD_MANUAL_PAY", "STUDY_LEAVE_SUBSIDY"):
                    manual_item_overrides.add(item_code)
            else:
                item_code = _raw_item_code(name_norm)
                display_name = raw_norm_to_display.get(name_norm, item_name)
                manual_item_codes.add(item_code)
                manual_raw_name_by_code[item_code] = display_name
                manual_raw_norms.add(name_norm)
        target_type = str(row.target_type or "").strip().upper()
        if target_type == "PERSON":
            _add_direct_or_redirect(
                row.target_value,
                item_code,
                item_name,
                amount,
                item_code,
                note="manual entry",
            )
            continue
        if target_type != "POOL":
            _add_qc(
                session,
                run_id,
                "MANUAL_ENTRY_INVALID",
                f"Manual entry target type invalid: {row.target_type}",
                {"target_type": row.target_type},
            )
            continue
        pool_code = str(row.target_value or "").strip()
        if pool_code not in (POOL_NURSING, POOL_DOCTOR):
            _add_qc(
                session,
                run_id,
                "MANUAL_ENTRY_INVALID",
                f"Manual entry pool code invalid: {row.target_value}",
                {"pool_code": row.target_value},
            )
            continue
        pool_totals[pool_code] += amount
        session.add(
            FactPool(
                run_id=run_id,
                pool_code=pool_code,
                source_item_code=item_code,
                amount=round_money(amount),
                note="manual entry",
            )
        )

    # Manual doctor workload pay (skip if new manual entries override)
    manual_rows = list(
        session.execute(
            select(RawManualDoctorWorkloadPay).where(RawManualDoctorWorkloadPay.run_id == run_id)
        ).scalars()
    )
    if "WORKLOAD_MANUAL_PAY" not in manual_item_overrides:
        for row in manual_rows:
            _add_direct_or_redirect(
                row.name,
                "WORKLOAD_MANUAL_PAY",
                "工作量",
                to_decimal(row.amount),
                "WORKLOAD_MANUAL_PAY",
            )

    # Manual pool adjust (e.g. study leave subsidy manual portion)
    manual_pool_rows = list(
        session.execute(
            select(RawManualPoolAdjust).where(RawManualPoolAdjust.run_id == run_id)
        ).scalars()
    )
    for row in manual_pool_rows:
        pool_code = str(row.pool_code or "").strip()
        if pool_code not in (POOL_NURSING, POOL_DOCTOR):
            continue
        amount = to_decimal(row.amount)
        if amount == 0:
            continue
        pool_totals[pool_code] += amount
        session.add(
            FactPool(
                run_id=run_id,
                pool_code=pool_code,
                source_item_code="MANUAL_POOL_ADJUST",
                amount=round_money(amount),
                note=row.note or "manual pool adjust",
            )
        )

    # Admission cert
    admission_amount = item_totals.get("ADMISSION_CERT_FEE", Decimal("0"))
    if admission_amount:
        unit = params.get("admission_cert_unit", Decimal("50"))
        total_paid = Decimal("0")
        for name, row in doctor_workload.items():
            count = to_decimal(row.admission_cert_count)
            if count <= 0:
                continue
            amount = unit * count
            total_paid += amount
            _add_direct_or_redirect(
                name,
                "ADMISSION_CERT_FEE",
                "住院证补贴",
                amount,
                "ADMISSION_CERT_FEE",
            )
        if total_paid != admission_amount:
            session.add(
                ReconcileItem(
                    run_id=run_id,
                    item_code="ADMISSION_CERT_FEE",
                    source_amount=round_money(admission_amount),
                    allocated_amount=round_money(total_paid),
                    delta=round_money(admission_amount - total_paid),
                    note="Admission cert residual",
                )
            )

    # Blood draw
    blood_amount = item_totals.get("BLOOD_DRAW_FEE", Decimal("0"))
    if blood_amount:
        nurse_weights = {
            name: to_decimal(row.blood_draw_count) for name, row in nurse_workload.items()
        }
        total_draw = sum(nurse_weights.values())
        if total_draw == 0:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Blood draw total is 0")
        else:
            alloc = allocate_by_weight(blood_amount, nurse_weights)
            for name, amount in alloc.items():
                _add_direct_or_redirect(
                    name,
                    "BLOOD_DRAW_FEE",
                    "抽血费",
                    amount,
                    "BLOOD_DRAW_FEE",
                )

    # Study leave subsidy (manual entries override, then legacy manual; no auto allocation)
    study_manual_rows = list(
        session.execute(
            select(RawManualStudyLeavePay).where(RawManualStudyLeavePay.run_id == run_id)
        ).scalars()
    )
    if "STUDY_LEAVE_SUBSIDY" in manual_item_overrides:
        pass
    elif study_manual_rows:
        for row in study_manual_rows:
            _add_direct_or_redirect(
                row.name,
                "STUDY_LEAVE_SUBSIDY",
                "进修产假补贴",
                to_decimal(row.amount),
                "STUDY_LEAVE_SUBSIDY",
            )
    else:
        study_amount = item_totals.get("STUDY_LEAVE_SUBSIDY", Decimal("0"))
        if study_amount:
            _add_qc(
                session,
                run_id,
                "MANUAL_REQUIRED",
                "Study leave subsidy requires manual allocation",
                {"item_code": "STUDY_LEAVE_SUBSIDY", "amount": float(study_amount)},
            )

    # Surplus
    surplus_amount = item_totals.get("SURPLUS", Decimal("0"))
    if surplus_amount:
        director_ratio = params.get("surplus_director_ratio", Decimal("0.15"))
        head_ratio = params.get("surplus_head_nurse_ratio", Decimal("0.05"))
        directors = [e.name for e in employees.values() if e.is_director]
        head_nurses = [e.name for e in employees.values() if e.is_head_nurse]
        fixed_total = Decimal("0")
        if directors:
            per = (surplus_amount * director_ratio) / Decimal(len(directors))
            fixed_total += surplus_amount * director_ratio
            for name in directors:
                _add_pay_detail(
                    session,
                    run_id,
                    name,
                    "SURPLUS",
                    "科室盈余",
                    per,
                    "SURPLUS",
                    PAY_SURPLUS,
                )
        if head_nurses:
            per = (surplus_amount * head_ratio) / Decimal(len(head_nurses))
            fixed_total += surplus_amount * head_ratio
            for name in head_nurses:
                _add_pay_detail(
                    session,
                    run_id,
                    name,
                    "SURPLUS",
                    "科室盈余",
                    per,
                    "SURPLUS",
                    PAY_SURPLUS,
                )
        remain = surplus_amount - fixed_total
        weights = {
            name: to_decimal(emp.perf_score)
            for name, emp in employees.items()
            if emp.eligible_for_surplus_weight and to_decimal(emp.perf_score) > 0
        }
        if remain and remain != 0:
            if not weights:
                _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Surplus weights total is 0")
            else:
                alloc = allocate_by_weight(remain, weights)
                for name, amount in alloc.items():
                    _add_pay_detail(
                        session,
                        run_id,
                        name,
                        "SURPLUS",
                        "科室盈余",
                        amount,
                        "SURPLUS",
                        PAY_SURPLUS,
                    )

    # Pool allocations: nursing
    nursing_pool_total = pool_totals.get(POOL_NURSING, Decimal("0"))
    if nursing_pool_total:
        scores = [
            to_decimal(row.score)
            for row in nurse_workload.values()
            if to_decimal(row.score) > 0
        ]
        avg_score = sum(scores) / len(scores) if scores else Decimal("0")
        coeff = params.get("head_nurse_score_coeff", Decimal("1.4"))
        weights = {}
        for name, row in nurse_workload.items():
            if name not in roster_names:
                continue
            score = to_decimal(row.score)
            emp = employees.get(name)
            if emp and emp.is_head_nurse:
                score = avg_score * coeff
            if score <= 0:
                continue
            weights[name] = score
        if avg_score > 0:
            for name, emp in employees.items():
                if (
                    name in roster_names
                    and emp.role_type == "nurse"
                    and emp.is_head_nurse
                    and name not in weights
                ):
                    weights[name] = avg_score * coeff
        if not weights:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Nursing pool weights total is 0")
        else:
            alloc = allocate_by_weight(nursing_pool_total, weights)
            for name, amount in alloc.items():
                session.add(
                    FactPoolAlloc(
                        run_id=run_id,
                        pool_code=POOL_NURSING,
                        name=name,
                        amount=round_money(amount),
                        weight=round_money(weights[name]),
                        note=None,
                    )
                )
                _add_pay_detail(
                    session,
                    run_id,
                    name,
                    "POOL_NURSING",
                    "护理池分配",
                    amount,
                    "POOL_NURSING",
                    PAY_POOL_NURSING,
                    POOL_NURSING,
                )

    # Pool allocations: doctor
    doctor_pool_total = pool_totals.get(POOL_DOCTOR, Decimal("0"))
    if doctor_pool_total:
        min_weight = params.get("doctor_pool_min_weight", Decimal("0.8"))
        weights = {}
        for name, row in doctor_workload.items():
            if name not in roster_names:
                continue
            if name not in employees or employees[name].role_type != "doctor":
                continue
            workload = to_decimal(row.workload)
            if workload <= 0:
                workload = min_weight
            weights[name] = workload
        if not weights:
            _add_qc(session, run_id, "DIVIDE_BY_ZERO", "Doctor pool weights total is 0")
        else:
            alloc = allocate_by_weight(doctor_pool_total, weights)
            for name, amount in alloc.items():
                session.add(
                    FactPoolAlloc(
                        run_id=run_id,
                        pool_code=POOL_DOCTOR,
                        name=name,
                        amount=round_money(amount),
                        weight=round_money(weights[name]),
                        note=None,
                    )
                )
                _add_pay_detail(
                    session,
                    run_id,
                    name,
                    "POOL_DOCTOR",
                    "医师池分配",
                    amount,
                    "POOL_DOCTOR",
                    PAY_POOL_DOCTOR,
                    POOL_DOCTOR,
                )

    session.flush()

    # Manual raw item reconcile helpers
    manual_raw_source_amounts: dict[str, Decimal] = {}
    skip_reconcile_codes: set[str] = set()
    unclassified_exclude_total = Decimal("0")
    for raw_norm in manual_raw_norms:
        code = _raw_item_code(raw_norm)
        amount = raw_norm_totals.get(raw_norm, Decimal("0"))
        manual_raw_source_amounts[code] = amount
        mapped_code = raw_norm_to_code.get(raw_norm)
        if mapped_code:
            behavior = behaviors.get(mapped_code)
            if behavior in (None, "UNCLASSIFIED", "RECON_ONLY"):
                skip_reconcile_codes.add(mapped_code)
        else:
            unclassified_exclude_total += amount

    detail_totals_by_code = {
        code: to_decimal(amount)
        for code, amount in session.execute(
            select(
                FactPayDetail.source_item_code,
                func.sum(FactPayDetail.amount),
            )
            .where(FactPayDetail.run_id == run_id)
            .group_by(FactPayDetail.source_item_code)
        ).all()
        if code
    }
    pool_totals_by_code = {
        code: to_decimal(amount)
        for code, amount in session.execute(
            select(
                FactPool.source_item_code,
                func.sum(FactPool.amount),
            )
            .where(FactPool.run_id == run_id)
            .group_by(FactPool.source_item_code)
        ).all()
        if code
    }

    # Reconcile
    reconcile_codes = set(item_totals.keys()) | manual_item_codes | set(manual_raw_source_amounts.keys())
    for code in reconcile_codes:
        if code in skip_reconcile_codes:
            continue
        source_amount = item_totals.get(code, Decimal("0"))
        if code == "OR_COST_ALLOC":
            session.add(
                ReconcileItem(
                    run_id=run_id,
                    item_code=code,
                    source_amount=round_money(source_amount),
                    allocated_amount=Decimal("0"),
                    delta=round_money(source_amount),
                    note="RECON_ONLY",
                )
            )
            continue
        if code == "UNCLASSIFIED_ITEM":
            source_amount = item_totals.get(code, Decimal("0")) - unclassified_exclude_total
            if source_amount <= 0:
                continue
            session.add(
                ReconcileItem(
                    run_id=run_id,
                    item_code=code,
                    source_amount=round_money(source_amount),
                    allocated_amount=Decimal("0"),
                    delta=round_money(source_amount),
                    note="UNCLASSIFIED",
                )
            )
            continue
        # admission cert already reconciled
        if code == "ADMISSION_CERT_FEE":
            continue
        if code in manual_raw_source_amounts:
            source_amount = manual_raw_source_amounts.get(code, Decimal("0"))
        direct_total = detail_totals_by_code.get(code, Decimal("0"))
        pool_total = pool_totals_by_code.get(code, Decimal("0"))
        allocated = direct_total + pool_total
        session.add(
            ReconcileItem(
                run_id=run_id,
                item_code=code,
                source_amount=round_money(source_amount),
                allocated_amount=round_money(allocated),
                delta=round_money(source_amount - allocated),
                note=f"RAW_NAME:{manual_raw_name_by_code[code]}" if code in manual_raw_name_by_code else None,
            )
        )
    session.flush()

    # Summary
    pay_rows = session.execute(
        select(FactPayDetail).where(FactPayDetail.run_id == run_id)
    ).scalars().all()
    summary = defaultdict(lambda: {
        "direct_total": Decimal("0"),
        "pool_nursing": Decimal("0"),
        "pool_doctor": Decimal("0"),
        "surplus": Decimal("0"),
    })
    for row in pay_rows:
        if row.pay_type == PAY_DIRECT:
            summary[row.name]["direct_total"] += to_decimal(row.amount)
        elif row.pay_type == PAY_POOL_NURSING:
            summary[row.name]["pool_nursing"] += to_decimal(row.amount)
        elif row.pay_type == PAY_POOL_DOCTOR:
            summary[row.name]["pool_doctor"] += to_decimal(row.amount)
        elif row.pay_type == PAY_SURPLUS:
            summary[row.name]["surplus"] += to_decimal(row.amount)

    for name, totals in summary.items():
        emp = employees.get(name)
        role = emp.role if emp else ""
        direct_total = round_money(totals["direct_total"])
        pool_nursing = round_money(totals["pool_nursing"])
        pool_doctor = round_money(totals["pool_doctor"])
        surplus = round_money(totals["surplus"])
        grand_total = round_money(direct_total + pool_nursing + pool_doctor + surplus)
        session.add(
            FactPaySummary(
                run_id=run_id,
                name=name,
                role=role,
                direct_total=direct_total,
                pool_nursing=pool_nursing,
                pool_doctor=pool_doctor,
                surplus=surplus,
                grand_total=grand_total,
            )
        )
    session.commit()

    rows = [
        {
            "name": r.name,
            "role": r.role,
            "direct_total": float(r.direct_total),
            "pool_nursing": float(r.pool_nursing),
            "pool_doctor": float(r.pool_doctor),
            "surplus": float(r.surplus),
            "grand_total": float(r.grand_total),
        }
        for r in session.execute(
            select(FactPaySummary).where(FactPaySummary.run_id == run_id)
        ).scalars()
    ]

    return {"rows": rows}
