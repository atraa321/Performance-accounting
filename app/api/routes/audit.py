"""
审计日志路由
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc

from app.api.deps import get_db
from app.models.audit import OperationLog

router = APIRouter(prefix="/audit-logs", tags=["审计日志"])


def _ensure_table(db):
    bind = db.get_bind()
    OperationLog.__table__.create(bind=bind, checkfirst=True)


@router.get("/")
def list_audit_logs(
    run_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    status: Optional[str] = None,
    operator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db=Depends(get_db)
):
    """获取审计日志列表"""
    _ensure_table(db)
    stmt = select(OperationLog)
    
    # 过滤条件
    if run_id is not None:
        stmt = stmt.where(OperationLog.run_id == run_id)
    if operation_type:
        stmt = stmt.where(OperationLog.operation_type == operation_type)
    if status:
        stmt = stmt.where(OperationLog.status == status)
    if operator:
        stmt = stmt.where(OperationLog.operator == operator)
    if start_date:
        stmt = stmt.where(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(OperationLog.created_at <= datetime.fromisoformat(end_date))
    
    # 排序和分页
    stmt = stmt.order_by(desc(OperationLog.created_at)).limit(limit).offset(offset)
    
    logs = db.execute(stmt).scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "run_id": log.run_id,
                "operation_type": log.operation_type,
                "operation_name": log.operation_name,
                "operator": log.operator,
                "details": log.details,
                "payload": log.payload,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "ip_address": log.ip_address,
            }
            for log in logs
        ],
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db=Depends(get_db)
):
    """获取审计统计信息"""
    _ensure_table(db)
    start_date = datetime.now() - timedelta(days=days)
    
    logs = db.execute(
        select(OperationLog).where(OperationLog.created_at >= start_date)
    ).scalars().all()
    
    # 统计各类操作数量
    type_stats = {}
    status_stats = {"SUCCESS": 0, "FAILED": 0}
    
    for log in logs:
        type_stats[log.operation_type] = type_stats.get(log.operation_type, 0) + 1
        status_stats[log.status] = status_stats.get(log.status, 0) + 1
    
    return {
        "period_days": days,
        "total_operations": len(logs),
        "by_type": type_stats,
        "by_status": status_stats,
        "success_rate": (status_stats["SUCCESS"] / len(logs) * 100) if logs else 0
    }


@router.get("/types")
def get_operation_types():
    """获取所有操作类型"""
    return {
        "types": [
            {"code": "RUN_MANAGEMENT", "name": "批次管理"},
            {"code": "DATA_IMPORT", "name": "数据导入"},
            {"code": "DATA_EDIT", "name": "数据编辑"},
            {"code": "CALCULATION", "name": "绩效计算"},
            {"code": "CONFIG_CHANGE", "name": "配置变更"},
            {"code": "DATA_EXPORT", "name": "数据导出"},
            {"code": "DATA_VALIDATION", "name": "数据验证"},
        ]
    }
