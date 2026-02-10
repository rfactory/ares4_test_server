from app.domains.action_authorization.policies.factory_enrollment.policy import FactoryEnrollmentPolicy

class FactoryEnrollmentPolicyProvider:
    def get_policy(self) -> FactoryEnrollmentPolicy:
        return FactoryEnrollmentPolicy()

factory_enrollment_policy_provider = FactoryEnrollmentPolicyProvider()