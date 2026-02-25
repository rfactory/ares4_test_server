# 애플리케이션을 위한 사용자 정의 예외 클래스

class AresException(Exception):
    """애플리케이션의 기본 예외 클래스."""
    pass

class AppLogicError(AresException):
    """일반적인 비즈니스 로직 관련 오류를 나타내는 예외."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ValidationError(AresException):
    """입력 데이터가 유효성 검사 규칙을 통과하지 못했을 때 발생하는 예외."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundError(AresException):
    """요청한 리소스를 찾을 수 없을 때 발생하는 예외."""
    def __init__(self, resource_name: str, resource_id):
        self.resource_name = resource_name
        self.resource_id = resource_id
        super().__init__(f"{resource_name} with ID '{resource_id}' not found.")

class PermissionDeniedError(AresException):
    """사용자가 권한 없는 작업을 시도했을 때 발생하는 예외."""
    def __init__(self, message: str = "You do not have permission to perform this action."):
        self.message = message
        super().__init__(self.message)

class ForbiddenError(AresException):
    """사용자가 정책에 의해 금지된 작업을 시도했을 때 발생하는 예외. (일반적인 권한이 있더라도)"""
    def __init__(self, message: str = "You are not allowed to perform this action."):
        self.message = message
        super().__init__(self.message)

class ConflictError(AresException):
    """요청이 현재 리소스의 상태와 충돌할 때 발생하는 예외 (예: 사용 중인 리소스 삭제)."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class DuplicateEntryError(AresException):
    """이미 존재하는 리소스를 생성하려고 시도했을 때 발생하는 예외."""
    def __init__(self, resource_name: str, conflicting_field: str, conflicting_value):
        self.resource_name = resource_name
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value
        super().__init__(f"{resource_name} with {conflicting_field} '{conflicting_value}' already exists.")

class AuthenticationError(AresException):
    """인증에 실패했을 때 발생하는 예외."""
    def __init__(self, message: str = "Authentication failed."):
        self.message = message
        super().__init__(self.message)

class AccessDeniedError(AresException):
    """권한이 거부되었을 때 발생하는 예외 (403 Forbidden)"""
    def __init__(self, message: str = "접근 권한이 없습니다."):
        self.message = message
        self.status_code = 403
        self.error_code = "ACCESS_DENIED"
        super().__init__(self.message)