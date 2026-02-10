from app.domains.action_authorization.validators.factory_enrollment.validator import FactoryEnrollmentValidator

class FactoryEnrollmentValidatorProvider:
    def get_validator(self) -> FactoryEnrollmentValidator:
        return FactoryEnrollmentValidator()

factory_enrollment_validator_provider = FactoryEnrollmentValidatorProvider()