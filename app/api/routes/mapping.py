from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import get_db
from app.calc.utils import normalize_item_name
from app.models.models import DictItemBehavior, DictItemMapping, RawHospitalPerfItem
from app.schemas.rule import (
    ItemMappingResponse,
    ItemMappingCreate,
    ItemMappingUpdate,
    ItemBehaviorResponse,
    ItemBehaviorCreate,
    ItemBehaviorUpdate
)

router = APIRouter(tags=["项目映射"])


def _get_behavior_by_item_code(db, item_code: str) -> Optional[DictItemBehavior]:
    return db.execute(
        select(DictItemBehavior).where(DictItemBehavior.item_code == item_code)
    ).scalar_one_or_none()


def _attach_behavior_type(db, mapping: DictItemMapping) -> DictItemMapping:
    behavior = _get_behavior_by_item_code(db, mapping.item_code)
    mapping.behavior_type = behavior.behavior_type if behavior else None
    return mapping


def _attach_behavior_type_bulk(db, mappings: List[DictItemMapping]) -> List[DictItemMapping]:
    item_codes = {m.item_code for m in mappings}
    if not item_codes:
        return mappings
    behavior_rows = db.execute(
        select(DictItemBehavior).where(DictItemBehavior.item_code.in_(item_codes))
    ).scalars().all()
    behavior_map = {row.item_code: row.behavior_type for row in behavior_rows}
    for mapping in mappings:
        mapping.behavior_type = behavior_map.get(mapping.item_code)
    return mappings


def _upsert_behavior(db, item_code: str, behavior_type: str) -> None:
    behavior = _get_behavior_by_item_code(db, item_code)
    if behavior:
        behavior.behavior_type = behavior_type
    else:
        db.add(DictItemBehavior(item_code=item_code, behavior_type=behavior_type))


# ==================== 项目映射管理 ====================

@router.get("/mappings", response_model=List[ItemMappingResponse])
def list_mappings(is_active: Optional[bool] = None, db=Depends(get_db)):
    """获取所有项目映射"""
    stmt = select(DictItemMapping)
    if is_active is not None:
        stmt = stmt.where(DictItemMapping.is_active == is_active)
    mappings = db.execute(stmt).scalars().all()
    return _attach_behavior_type_bulk(db, mappings)


@router.get("/mappings/{mapping_id}", response_model=ItemMappingResponse)
def get_mapping(mapping_id: int, db=Depends(get_db)):
    """获取单个项目映射"""
    mapping = db.get(DictItemMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return _attach_behavior_type(db, mapping)


@router.post("/mappings", response_model=ItemMappingResponse)
def create_mapping(payload: ItemMappingCreate, db=Depends(get_db)):
    """创建项目映射"""
    mapping = DictItemMapping(
        raw_item_name=payload.raw_item_name,
        item_code=payload.item_code,
        priority=payload.priority,
        is_active=payload.is_active
    )
    db.add(mapping)
    if payload.behavior_type:
        _upsert_behavior(db, payload.item_code, payload.behavior_type)
    db.commit()
    db.refresh(mapping)
    return _attach_behavior_type(db, mapping)


@router.put("/mappings/{mapping_id}", response_model=ItemMappingResponse)
def update_mapping(mapping_id: int, payload: ItemMappingUpdate, db=Depends(get_db)):
    """更新项目映射"""
    mapping = db.get(DictItemMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    if payload.raw_item_name is not None:
        mapping.raw_item_name = payload.raw_item_name
    if payload.item_code is not None:
        mapping.item_code = payload.item_code
    if payload.priority is not None:
        mapping.priority = payload.priority
    if payload.is_active is not None:
        mapping.is_active = payload.is_active
    if payload.behavior_type:
        _upsert_behavior(db, mapping.item_code, payload.behavior_type)
    
    db.commit()
    db.refresh(mapping)
    return _attach_behavior_type(db, mapping)


@router.delete("/mappings/{mapping_id}")
def delete_mapping(mapping_id: int, db=Depends(get_db)):
    """删除项目映射（软删除，设置为不活跃）"""
    mapping = db.get(DictItemMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    mapping.is_active = False
    db.commit()
    return {"status": "deleted", "id": mapping_id}


@router.post("/mappings/batch")
def batch_create_mappings(payload: List[ItemMappingCreate], db=Depends(get_db)):
    """批量创建项目映射"""
    created = 0
    for item in payload:
        mapping = DictItemMapping(
            raw_item_name=item.raw_item_name,
            item_code=item.item_code,
            priority=item.priority,
            is_active=item.is_active
        )
        db.add(mapping)
        if item.behavior_type:
            _upsert_behavior(db, item.item_code, item.behavior_type)
        created += 1
    db.commit()
    return {"created": created}


@router.get("/mapping/unmatched")
def get_unmatched(run_id: Optional[int] = None, db=Depends(get_db)):
    """获取未映射的项目"""
    mappings = db.execute(select(DictItemMapping).where(DictItemMapping.is_active == True)).scalars().all()
    mapping_keys = [m.raw_item_name for m in mappings]
    
    stmt = select(RawHospitalPerfItem)
    if run_id:
        stmt = stmt.where(RawHospitalPerfItem.run_id == run_id)
    
    items = db.execute(stmt).scalars().all()
    unmatched = set()
    for item in items:
        norm = item.item_name_norm or normalize_item_name(item.item_name)
        if not any(key in norm for key in mapping_keys):
            unmatched.add(item.item_name)
    return {"items": sorted(unmatched), "count": len(unmatched)}


# ==================== 项目行为管理 ====================

@router.get("/item-behaviors", response_model=List[ItemBehaviorResponse])
def list_behaviors(db=Depends(get_db)):
    """获取所有项目行为"""
    behaviors = db.execute(select(DictItemBehavior)).scalars().all()
    return behaviors


@router.get("/item-behaviors/{behavior_id}", response_model=ItemBehaviorResponse)
def get_behavior(behavior_id: int, db=Depends(get_db)):
    """获取单个项目行为"""
    behavior = db.get(DictItemBehavior, behavior_id)
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    return behavior


@router.post("/item-behaviors", response_model=ItemBehaviorResponse)
def create_behavior(payload: ItemBehaviorCreate, db=Depends(get_db)):
    """创建项目行为"""
    # 检查是否已存在
    existing = db.execute(
        select(DictItemBehavior).where(DictItemBehavior.item_code == payload.item_code)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Behavior for this item_code already exists")
    
    behavior = DictItemBehavior(
        item_code=payload.item_code,
        behavior_type=payload.behavior_type
    )
    db.add(behavior)
    db.commit()
    db.refresh(behavior)
    return behavior


@router.put("/item-behaviors/{behavior_id}", response_model=ItemBehaviorResponse)
def update_behavior(behavior_id: int, payload: ItemBehaviorUpdate, db=Depends(get_db)):
    """更新项目行为"""
    behavior = db.get(DictItemBehavior, behavior_id)
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    behavior.behavior_type = payload.behavior_type
    db.commit()
    db.refresh(behavior)
    return behavior


@router.delete("/item-behaviors/{behavior_id}")
def delete_behavior(behavior_id: int, db=Depends(get_db)):
    """删除项目行为"""
    behavior = db.get(DictItemBehavior, behavior_id)
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior not found")
    
    db.delete(behavior)
    db.commit()
    return {"status": "deleted", "id": behavior_id}


@router.get("/item-behaviors/types/available")
def get_available_behavior_types():
    """获取可用的行为类型"""
    return {
        "types": [
            {"code": "DIRECT", "name": "直接发放", "description": "直接分配给个人"},
            {"code": "POOL_NURSING", "name": "护理池", "description": "进入护理池统一分配"},
            {"code": "POOL_DOCTOR", "name": "医师池", "description": "进入医师池统一分配"},
            {"code": "SPECIAL", "name": "特殊规则", "description": "使用特殊计算规则"},
            {"code": "RECON_ONLY", "name": "仅对账", "description": "不分配，仅用于对账"},
            {"code": "UNCLASSIFIED", "name": "未分类", "description": "未映射的项目"}
        ]
    }


# ==================== 兼容旧接口 ====================

@router.post("/mapping")
def save_mapping(payload: List[Dict], db=Depends(get_db)):
    """批量保存映射（兼容旧接口）"""
    created = 0
    for item in payload:
        raw_name = item.get("raw_item_name")
        item_code = item.get("item_code")
        priority = item.get("priority", 100)
        if not raw_name or not item_code:
            continue
        db.add(
            DictItemMapping(
                raw_item_name=raw_name,
                item_code=item_code,
                priority=priority,
                is_active=True,
            )
        )
        created += 1
    db.commit()
    return {"created": created}


@router.post("/item-behavior")
def save_behavior(payload: List[Dict], db=Depends(get_db)):
    """批量保存行为（兼容旧接口）"""
    created = 0
    for item in payload:
        item_code = item.get("item_code")
        behavior_type = item.get("behavior_type")
        if not item_code or not behavior_type:
            continue
        db.add(DictItemBehavior(item_code=item_code, behavior_type=behavior_type))
        created += 1
    db.commit()
    return {"created": created}
