"""
数据校验模块
用于在导入和计算前进行业务规则校验
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy import select

from app.models.models import (
    RawHospitalPerfItem,
    RawRoster,
    RawNightShift,
    RawReadingFee,
    RawDoctorWorkload,
    RawNurseWorkload,
    QcIssue
)
from app.calc.utils import to_decimal


class ValidationResult:
    """校验结果"""
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.info: List[Dict[str, Any]] = []
    
    def add_error(self, message: str, **kwargs):
        self.errors.append({"message": message, **kwargs})
    
    def add_warning(self, message: str, **kwargs):
        self.warnings.append({"message": message, **kwargs})
    
    def add_info(self, message: str, **kwargs):
        self.info.append({"message": message, **kwargs})
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }


def validate_run_data(session, run_id: int) -> ValidationResult:
    """
    验证一个 run 的所有数据
    """
    result = ValidationResult()
    
    # 1. 验证基础数据完整性
    _validate_basic_data(session, run_id, result)
    
    # 2. 验证人员数据一致性
    _validate_employee_consistency(session, run_id, result)
    
    # 3. 验证金额合理性
    _validate_amount_reasonableness(session, run_id, result)
    
    # 4. 验证业务规则
    _validate_business_rules(session, run_id, result)
    
    return result


def _validate_basic_data(session, run_id: int, result: ValidationResult):
    """验证基础数据完整性"""
    
    # 检查是否有院发绩效表数据
    perf_items = session.execute(
        select(RawHospitalPerfItem).where(RawHospitalPerfItem.run_id == run_id)
    ).scalars().all()
    if not perf_items:
        result.add_error("缺少院发绩效表数据", issue_type="MISSING_DATA")
    else:
        result.add_info(f"院发绩效表共 {len(perf_items)} 条记录")
    
    # 检查是否有发放名单
    roster = session.execute(
        select(RawRoster).where(RawRoster.run_id == run_id)
    ).scalars().all()
    if not roster:
        result.add_error("缺少绩效发放名单", issue_type="MISSING_DATA")
    else:
        result.add_info(f"发放名单共 {len(roster)} 人")
    
    # 检查金额是否有负数
    for item in perf_items:
        if to_decimal(item.amount) < 0:
            result.add_warning(
                f"院发绩效表存在负数金额：{item.item_name} = {item.amount}",
                issue_type="NEGATIVE_AMOUNT",
                item_name=item.item_name,
                amount=float(item.amount)
            )


def _validate_employee_consistency(session, run_id: int, result: ValidationResult):
    """验证人员数据一致性"""
    
    # 获取发放名单中的所有人员
    roster = session.execute(
        select(RawRoster).where(RawRoster.run_id == run_id)
    ).scalars().all()
    roster_names = {r.name for r in roster}
    
    if not roster_names:
        return
    
    # 检查夜班统计中的人员
    night_shifts = session.execute(
        select(RawNightShift).where(RawNightShift.run_id == run_id)
    ).scalars().all()
    for ns in night_shifts:
        if ns.name not in roster_names:
            result.add_warning(
                f"夜班统计中的人员 '{ns.name}' 不在发放名单中",
                issue_type="EMPLOYEE_NOT_IN_ROSTER",
                name=ns.name,
                source="夜班统计"
            )
    
    # 检查医师工作量中的人员
    doctor_workload = session.execute(
        select(RawDoctorWorkload).where(RawDoctorWorkload.run_id == run_id)
    ).scalars().all()
    for dw in doctor_workload:
        if dw.name not in roster_names:
            result.add_warning(
                f"医师工作量中的人员 '{dw.name}' 不在发放名单中",
                issue_type="EMPLOYEE_NOT_IN_ROSTER",
                name=dw.name,
                source="医师工作量"
            )
    
    # 检查护士工作量中的人员
    nurse_workload = session.execute(
        select(RawNurseWorkload).where(RawNurseWorkload.run_id == run_id)
    ).scalars().all()
    for nw in nurse_workload:
        if nw.name not in roster_names:
            result.add_warning(
                f"护士工作量中的人员 '{nw.name}' 不在发放名单中",
                issue_type="EMPLOYEE_NOT_IN_ROSTER",
                name=nw.name,
                source="护士工作量"
            )
    
    # 检查判读费中的外部人员
    reading_fees = session.execute(
        select(RawReadingFee).where(RawReadingFee.run_id == run_id)
    ).scalars().all()
    external_doctors = set()
    for rf in reading_fees:
        if rf.name not in roster_names:
            external_doctors.add(rf.name)
    
    if external_doctors:
        result.add_info(
            f"判读费中发现 {len(external_doctors)} 位外部医师：{', '.join(sorted(external_doctors))}",
            issue_type="EXTERNAL_DOCTORS",
            names=list(external_doctors)
        )


def _validate_amount_reasonableness(session, run_id: int, result: ValidationResult):
    """验证金额合理性"""
    
    # 检查绩效分数是否合理
    roster = session.execute(
        select(RawRoster).where(RawRoster.run_id == run_id)
    ).scalars().all()
    
    for r in roster:
        score = to_decimal(r.perf_score)
        if score < 0:
            result.add_error(
                f"人员 '{r.name}' 的绩效分数为负数：{score}",
                issue_type="INVALID_SCORE",
                name=r.name,
                score=float(score)
            )
        elif score > 1000:
            result.add_warning(
                f"人员 '{r.name}' 的绩效分数异常高：{score}",
                issue_type="UNUSUAL_SCORE",
                name=r.name,
                score=float(score)
            )
    
    # 检查夜班数是否合理
    night_shifts = session.execute(
        select(RawNightShift).where(RawNightShift.run_id == run_id)
    ).scalars().all()
    
    for ns in night_shifts:
        count = to_decimal(ns.night_count)
        if count < 0:
            result.add_error(
                f"人员 '{ns.name}' 的夜班数为负数：{count}",
                issue_type="INVALID_NIGHT_COUNT",
                name=ns.name,
                count=float(count)
            )
        elif count > 31:
            result.add_warning(
                f"人员 '{ns.name}' 的夜班数超过31天：{count}",
                issue_type="UNUSUAL_NIGHT_COUNT",
                name=ns.name,
                count=float(count)
            )


def _validate_business_rules(session, run_id: int, result: ValidationResult):
    """验证业务规则"""
    
    roster = session.execute(
        select(RawRoster).where(RawRoster.run_id == run_id)
    ).scalars().all()
    
    # 检查是否有科主任
    directors = [r for r in roster if "主任" in r.role and "副" not in r.role]
    if not directors:
        result.add_warning(
            "发放名单中未找到科主任",
            issue_type="NO_DIRECTOR"
        )
    elif len(directors) > 1:
        result.add_info(
            f"发放名单中有 {len(directors)} 位科主任：{', '.join([d.name for d in directors])}",
            issue_type="MULTIPLE_DIRECTORS"
        )
    
    # 检查是否有护士长
    head_nurses = [r for r in roster if "护士长" in r.role]
    if not head_nurses:
        result.add_warning(
            "发放名单中未找到护士长",
            issue_type="NO_HEAD_NURSE"
        )
    
    # 检查医师和护士的比例
    doctors = [r for r in roster if "医师" in r.role or "医生" in r.role]
    nurses = [r for r in roster if "护士" in r.role or "护理" in r.role]
    
    result.add_info(
        f"人员构成：医师 {len(doctors)} 人，护士 {len(nurses)} 人",
        issue_type="STAFF_COMPOSITION",
        doctors=len(doctors),
        nurses=len(nurses)
    )


def save_validation_results_to_qc(session, run_id: int, validation_result: ValidationResult):
    """将校验结果保存到 QC 表"""
    
    for error in validation_result.errors:
        session.add(QcIssue(
            run_id=run_id,
            issue_type=error.get("issue_type", "VALIDATION_ERROR"),
            message=error["message"],
            severity="ERROR",
            payload=error
        ))
    
    for warning in validation_result.warnings:
        session.add(QcIssue(
            run_id=run_id,
            issue_type=warning.get("issue_type", "VALIDATION_WARNING"),
            message=warning["message"],
            severity="WARN",
            payload=warning
        ))
    
    session.commit()
