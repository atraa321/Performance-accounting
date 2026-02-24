from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import get_db
from app.core.config import DEFAULT_RULE_SET_CODE
from app.models.models import RuleSet, RuleParam
from app.schemas.rule import RuleParamResponse, RuleParamUpdate, RuleParamBatchUpdate

router = APIRouter(prefix="/rule-params", tags=["规则参数"])

OBSOLETE_PARAM_KEYS = {
    "doctor_night_unit",
    "nurse_night_unit",
}


def _get_default_rule_set(db):
    """获取默认规则集"""
    rule_set = db.execute(
        select(RuleSet).where(RuleSet.code == DEFAULT_RULE_SET_CODE)
    ).scalar_one_or_none()
    if not rule_set:
        raise HTTPException(status_code=404, detail="Default rule set not found")
    return rule_set


@router.get("", response_model=List[RuleParamResponse])
def list_rule_params(db=Depends(get_db)):
    """获取所有规则参数"""
    rule_set = _get_default_rule_set(db)
    params = db.execute(
        select(RuleParam).where(RuleParam.rule_set_id == rule_set.id)
    ).scalars().all()
    return params


@router.get("/{param_key}", response_model=RuleParamResponse)
def get_rule_param(param_key: str, db=Depends(get_db)):
    """获取单个规则参数"""
    rule_set = _get_default_rule_set(db)
    param = db.execute(
        select(RuleParam).where(
            RuleParam.rule_set_id == rule_set.id,
            RuleParam.param_key == param_key
        )
    ).scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail=f"Parameter {param_key} not found")
    return param


@router.put("/{param_key}", response_model=RuleParamResponse)
def update_rule_param(param_key: str, payload: RuleParamUpdate, db=Depends(get_db)):
    """更新单个规则参数"""
    rule_set = _get_default_rule_set(db)
    param = db.execute(
        select(RuleParam).where(
            RuleParam.rule_set_id == rule_set.id,
            RuleParam.param_key == param_key
        )
    ).scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail=f"Parameter {param_key} not found")
    
    param.param_value = payload.param_value
    if payload.param_value_num is not None:
        param.param_value_num = payload.param_value_num
    if payload.param_desc is not None:
        param.param_desc = payload.param_desc
    
    db.commit()
    db.refresh(param)
    return param


@router.post("/batch-update")
def batch_update_rule_params(payload: RuleParamBatchUpdate, db=Depends(get_db)):
    """批量更新规则参数"""
    rule_set = _get_default_rule_set(db)
    updated_count = 0
    
    for update in payload.updates:
        param_key = update.get("param_key")
        if not param_key:
            continue
        
        param = db.execute(
            select(RuleParam).where(
                RuleParam.rule_set_id == rule_set.id,
                RuleParam.param_key == param_key
            )
        ).scalar_one_or_none()
        
        if not param:
            continue
        
        if "param_value" in update:
            param.param_value = str(update["param_value"])
        if "param_value_num" in update:
            param.param_value_num = float(update["param_value_num"]) if update["param_value_num"] is not None else None
        if "param_desc" in update:
            param.param_desc = str(update["param_desc"]) if update["param_desc"] is not None else None
        
        updated_count += 1
    
    db.commit()
    return {"updated": updated_count}


@router.get("/grouped/by-category")
def get_params_by_category(db=Depends(get_db)):
    """按类别分组获取规则参数（便于前端展示）"""
    rule_set = _get_default_rule_set(db)
    params = db.execute(
        select(RuleParam).where(RuleParam.rule_set_id == rule_set.id)
    ).scalars().all()
    
    # 按业务逻辑分组
    categories: dict[str, list[dict]] = {
        "判读费分配": [],
        "床补分配": [],
        "护理池分配": [],
        "医师池分配": [],
        "科室盈余分配": [],
        "其他": []
    }
    
    for param in params:
        key = param.param_key
        if key in OBSOLETE_PARAM_KEYS:
            continue
        param_dict = {
            "id": param.id,
            "param_key": param.param_key,
            "param_value": param.param_value,
            "param_value_num": param.param_value_num,
            "param_desc": param.param_desc or _get_param_description(key)
        }
        
        if "lab" in key or "reading" in key:
            categories["判读费分配"].append(param_dict)
        elif "bed" in key:
            categories["床补分配"].append(param_dict)
        elif "nurse" in key or "head_nurse" in key:
            categories["护理池分配"].append(param_dict)
        elif "doctor_pool" in key:
            categories["医师池分配"].append(param_dict)
        elif "surplus" in key:
            categories["科室盈余分配"].append(param_dict)
        else:
            categories["其他"].append(param_dict)
    
    return categories


def _get_param_description(param_key: str) -> str:
    """获取参数的中文描述"""
    descriptions = {
        "lab_doctor_ratio": "化验判读费医师比例",
        "lab_nurse_ratio": "化验判读费护理池比例",
        "lead_reading_director_ratio": "科主任判读费主任比例",
        "lead_reading_deputy_ratio": "科主任判读费副主任比例",
        "lead_reading_head_nurse_ratio": "科主任判读费护士长比例",
        "bed_subsidy_doctor_ratio": "床补医师比例",
        "bed_subsidy_nurse_ratio": "床补护理池比例",
        "head_nurse_score_coeff": "护士长分数系数",
        "doctor_pool_min_weight": "医师池最小权重（门诊医师）",
        "surplus_director_ratio": "科室盈余主任比例",
        "surplus_head_nurse_ratio": "科室盈余护士长比例",
        "admission_cert_unit": "住院证单价（元）",
    }
    return descriptions.get(param_key, param_key)
