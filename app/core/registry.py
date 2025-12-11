from typing import Optional

# Forward declaration to avoid circular imports
class CommandDispatchRepository:
    pass

class AppRegistry:
    """
    애플리케이션의 생명주기 동안 관리되는 주요 컴포넌트 인스턴스를 저장하는 전역 레지스트리입니다.
    의존성 주입(Dependency Injection)을 중앙에서 관리하는 역할을 합니다.
    """
    command_dispatch_repository: Optional[CommandDispatchRepository] = None

app_registry = AppRegistry()
