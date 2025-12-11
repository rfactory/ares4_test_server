from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.domains.services.telemetry_validation.services.telemetry_validation_service import telemetry_validation_service

class TelemetryValidationProviders:
    def validate_incoming_telemetry(
        self,
        db: Session,
        user_email: str,
        device_uuid_str: str,
        component_type: str,
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Provides a stable interface to validate incoming telemetry data.
        """
        return telemetry_validation_service.validate_incoming_telemetry(
            db=db,
            user_email=user_email,
            device_uuid_str=device_uuid_str,
            component_type=component_type,
            payload=payload
        )

telemetry_validation_providers = TelemetryValidationProviders()
