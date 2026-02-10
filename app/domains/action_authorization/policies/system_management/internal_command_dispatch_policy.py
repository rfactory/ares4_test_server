from sqlalchemy.orm import Session
from app.models.objects.user import User
from app.domains.inter_domain.command_dispatch import command_dispatch_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class InternalCommandDispatchPolicy:
    def execute(self, db: Session, *, topic: str, command: dict) -> dict:
        try:
            # 1. 시스템 액터 식별 (ID 1 시스템 유저를 여기서 찾음)
            system_user = db.query(User).filter(User.id == 1).first()
            
            # 2. 실질적인 명령 발행 (Command Service)
            command_dispatch_provider.publish_command(
                db=db,
                topic=topic,
                command=command,
                actor_user=system_user
            )

            # 3. Ares Aegis: 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="INTERNAL_MQTT_DISPATCH",
                description=f"Internal command dispatched to {topic}",
                actor_user=system_user,
                details={"topic": topic, "command": command}
            )

            # 4. 최종 확정 (커밋)
            db.commit()
            return {"message": "Internal command dispatched and logged successfully."}

        except Exception as e:
            db.rollback()
            raise e

internal_command_dispatch_policy = InternalCommandDispatchPolicy()