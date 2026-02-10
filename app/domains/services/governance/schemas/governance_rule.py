from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GovernanceRuleBase(BaseModel):
    rule_name: str = Field(..., description="규칙의 고유한 이름")
    description: Optional[str] = Field(None, description="규칙에 대한 상세 설명")
    actor_role_id: int = Field(..., description="규칙을 실행하는 주체 역할의 ID")
    action: str = Field(..., description="규칙이 적용되는 행동 (예: 'assign_role', 'context_switch')")
    target_role_id: Optional[int] = Field(None, description="행동의 대상이 되는 역할의 ID")
    context: str = Field(..., description="규칙이 적용되는 컨텍스트 (SYSTEM, ORGANIZATION)")
    allow: bool = Field(True, description="규칙에 따른 행동 허용 여부")
    priority: int = Field(100, description="규칙의 우선순위 (낮을수록 높음)")
    conditions: Optional[Dict[str, Any]] = Field(None, description="추가적인 복잡한 조건을 정의하는 JSON 필드")

class GovernanceRuleCreate(GovernanceRuleBase):
    pass

class GovernanceRuleUpdate(BaseModel):
    description: Optional[str] = None
    actor_role_id: Optional[int] = None
    action: Optional[str] = None
    target_role_id: Optional[int] = None
    context: Optional[str] = None
    allow: Optional[bool] = None
    priority: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None

class GovernanceRuleRead(GovernanceRuleBase):
    id: int

    class Config:
        from_attributes = True
