from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Any


class RuleParamResponse(BaseModel):
    id: int
    param_key: str
    param_value: str
    param_value_num: Optional[float] = None
    param_desc: Optional[str] = None

    class Config:
        from_attributes = True


class RuleParamUpdate(BaseModel):
    param_value: str
    param_value_num: Optional[float] = None
    param_desc: Optional[str] = None


class RuleParamBatchUpdate(BaseModel):
    updates: List[Dict[str, Any]]


class ItemMappingResponse(BaseModel):
    id: int
    raw_item_name: str
    item_code: str
    priority: int
    is_active: bool
    behavior_type: Optional[str] = None

    class Config:
        from_attributes = True


class ItemMappingCreate(BaseModel):
    raw_item_name: str
    item_code: str
    priority: int = 100
    is_active: bool = True
    behavior_type: Optional[str] = None


class ItemMappingUpdate(BaseModel):
    raw_item_name: Optional[str] = None
    item_code: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    behavior_type: Optional[str] = None


class ItemBehaviorResponse(BaseModel):
    id: int
    item_code: str
    behavior_type: str

    class Config:
        from_attributes = True


class ItemBehaviorCreate(BaseModel):
    item_code: str
    behavior_type: str


class ItemBehaviorUpdate(BaseModel):
    behavior_type: str
