from sqlalchemy.orm import Session
import sqlalchemy as sa
from typing import List, Optional

from app.core.crud_base import CRUDBase
from app.models.objects.governance import GovernanceRule
from app.domains.services.governance.schemas.governance_rule import GovernanceRuleCreate, GovernanceRuleUpdate

class CRUDGovernanceRule(CRUDBase[GovernanceRule, GovernanceRuleCreate, GovernanceRuleUpdate]):
    def get_by_rule_name(self, db: Session, *, rule_name: str) -> Optional[GovernanceRule]:
        return db.query(self.model).filter(self.model.rule_name == rule_name).first()
    
    def find_matching_rules(
        self, 
        db: Session, 
        *, 
        actor_role_id: int,
        action: str,
        context: str,
        target_role_id: Optional[int] = None
    ) -> List[GovernanceRule]:
        """
        주어진 조건에 맞는 모든 거버넌스 규칙을 우선순위에 따라 조회합니다.
        대상 역할 ID가 명시된 규칙과, 대상 역할 ID가 없는 일반 규칙을 모두 포함합니다.
        """
        query = db.query(self.model).filter(
            self.model.actor_role_id == actor_role_id,
            self.model.action == action,
            self.model.context == context,
            sa.or_(
                self.model.target_role_id == target_role_id,
                self.model.target_role_id.is_(None)
            )
        )
        return query.order_by(self.model.priority).all()


governance_rule_crud = CRUDGovernanceRule(GovernanceRule)
