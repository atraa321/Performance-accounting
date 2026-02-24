"""
审计日志工具
用于记录系统操作日志
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.audit import OperationLog


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        operation_type: str,
        operation_name: str,
        run_id: Optional[int] = None,
        operator: Optional[str] = None,
        details: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录操作日志"""
        log = OperationLog(
            run_id=run_id,
            operation_type=operation_type,
            operation_name=operation_name,
            operator=operator,
            details=details,
            payload=payload,
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        self.db.commit()
        return log
    
    def log_run_created(self, run_id: int, month: str, dept_name: str, operator: Optional[str] = None):
        """记录批次创建"""
        return self.log(
            operation_type="RUN_MANAGEMENT",
            operation_name="创建核算批次",
            run_id=run_id,
            operator=operator,
            details=f"创建核算批次：{month} - {dept_name}",
            payload={"month": month, "dept_name": dept_name}
        )
    
    def log_excel_imported(self, run_id: int, stats: Dict[str, int], operator: Optional[str] = None):
        """记录Excel导入"""
        total_rows = sum(stats.values())
        return self.log(
            operation_type="DATA_IMPORT",
            operation_name="导入Excel数据",
            run_id=run_id,
            operator=operator,
            details=f"导入Excel数据，共 {total_rows} 条记录",
            payload={"stats": stats}
        )
    
    def log_calculation(self, run_id: int, result: Dict[str, Any], operator: Optional[str] = None):
        """记录计算操作"""
        row_count = len(result.get("rows", []))
        return self.log(
            operation_type="CALCULATION",
            operation_name="执行绩效计算",
            run_id=run_id,
            operator=operator,
            details=f"执行绩效计算，生成 {row_count} 条汇总记录",
            payload={"row_count": row_count}
        )
    
    def log_run_locked(self, run_id: int, operator: Optional[str] = None):
        """记录批次锁定"""
        return self.log(
            operation_type="RUN_MANAGEMENT",
            operation_name="锁定核算批次",
            run_id=run_id,
            operator=operator,
            details=f"锁定核算批次 {run_id}"
        )
    
    def log_rule_param_updated(self, param_key: str, old_value: str, new_value: str, operator: Optional[str] = None):
        """记录规则参数更新"""
        return self.log(
            operation_type="CONFIG_CHANGE",
            operation_name="更新规则参数",
            operator=operator,
            details=f"更新规则参数 {param_key}: {old_value} -> {new_value}",
            payload={"param_key": param_key, "old_value": old_value, "new_value": new_value}
        )
    
    def log_mapping_created(self, raw_item_name: str, item_code: str, operator: Optional[str] = None):
        """记录项目映射创建"""
        return self.log(
            operation_type="CONFIG_CHANGE",
            operation_name="创建项目映射",
            operator=operator,
            details=f"创建项目映射：{raw_item_name} -> {item_code}",
            payload={"raw_item_name": raw_item_name, "item_code": item_code}
        )
    
    def log_export(self, run_id: int, export_type: str = "excel", operator: Optional[str] = None):
        """记录导出操作"""
        return self.log(
            operation_type="DATA_EXPORT",
            operation_name=f"导出{export_type.upper()}",
            run_id=run_id,
            operator=operator,
            details=f"导出批次 {run_id} 的数据为 {export_type} 格式"
        )
    
    def log_error(self, operation_type: str, operation_name: str, error_message: str, 
                  run_id: Optional[int] = None, operator: Optional[str] = None):
        """记录错误"""
        return self.log(
            operation_type=operation_type,
            operation_name=operation_name,
            run_id=run_id,
            operator=operator,
            status="FAILED",
            error_message=error_message,
            details=f"操作失败：{error_message}"
        )


def get_audit_logger(db: Session) -> AuditLogger:
    """获取审计日志记录器"""
    return AuditLogger(db)
