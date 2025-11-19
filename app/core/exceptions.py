# Custom exception classes for the application

class AresException(Exception):
    """Base exception class for the application."""
    pass

class NotFoundError(AresException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_name: str, resource_id):
        self.resource_name = resource_name
        self.resource_id = resource_id
        super().__init__(f"{resource_name} with ID '{resource_id}' not found.")

class PermissionDeniedError(AresException):
    """Raised when a user attempts an action they are not authorized to perform."""
    def __init__(self, message: str = "You do not have permission to perform this action."):
        self.message = message
        super().__init__(self.message)

class DuplicateEntryError(AresException):
    """Raised when attempting to create a resource that already exists."""
    def __init__(self, resource_name: str, conflicting_field: str, conflicting_value):
        self.resource_name = resource_name
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value
        super().__init__(f"{resource_name} with {conflicting_field} '{conflicting_value}' already exists.")
