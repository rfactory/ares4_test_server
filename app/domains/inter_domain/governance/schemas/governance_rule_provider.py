"""
이 파일은 governance 도메인의 '규칙(Rule)' 관련 스키마를 다른 도메인에 안전하게 노출(re-export)합니다.
"""
# Service 계층에 정의된 원본 스키마를 가져옵니다.
from app.domains.services.governance.schemas.governance_rule import (
    GovernanceRuleRead, 
    GovernanceRuleCreate, 
    GovernanceRuleUpdate
)