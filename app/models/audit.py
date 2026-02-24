"""
操作日志模型
用于记录所有关键操作，支持审计追踪
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.core.db import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, nullable=True)  # 关联的批次ID（如果有）
    operation_type = Column(String(50), nullable=False)  # 操作类型
    operation_name = Column(String(200), nullable=False)  # 操作名称
    operator = Column(String(100), nullable=True)  # 操作人（预留，后续接入用户系统）
    details = Column(Text, nullable=True)  # 操作详情
    payload = Column(JSON, nullable=True)  # 操作数据（JSON格式）
    status = Column(String(20), nullable=False, default="SUCCESS")  # SUCCESS/FAILED
    error_message = Column(Text, nullable=True)  # 错误信息（如果失败）
    created_at = Column(DateTime, nullable=False, server_default=func.now())  # 操作时间
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(String(500), nullable=True)  # 用户代理
