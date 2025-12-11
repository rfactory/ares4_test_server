import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.core.registry import app_registry # Access the global registry

logger = logging.getLogger(__name__)

def publish_command(db: Session, *, topic: str, command: Dict, actor_user: Optional[User]):
    """
    AppRegistry에 등록된 CommandDispatchRepository를 통해 명령 메시지를 발행합니다.
    """
    if not app_registry.command_dispatch_repository:
        logger.error("CommandDispatchRepository is not initialized in AppRegistry.")
        raise RuntimeError("CommandDispatchRepository not available. Application might not be fully initialized.")
    
    app_registry.command_dispatch_repository.publish_command(
        db=db,
        topic=topic,
        command=command,
        actor_user=actor_user
    )