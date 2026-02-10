from app.domains.services.factory_identity.services.identity_command_service import FactoryIdentityService

class FactoryIdentityCommandProvider:
    def get_service(self) -> FactoryIdentityService:
        return FactoryIdentityService()

factory_identity_command_provider = FactoryIdentityCommandProvider()