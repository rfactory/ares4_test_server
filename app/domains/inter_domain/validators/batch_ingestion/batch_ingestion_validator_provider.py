from typing import Tuple, Optional, List, Dict, Any
from app.domains.action_authorization.validators.batch_ingestion.batch_ingestion_validator import batch_ingestion_validator

class BatchIngestionValidatorProvider:
    def validate_all(
        self, 
        *, 
        device: Optional[Any], 
        telemetry_data: List[Dict[str, Any]], 
        image_files: List[Any]
    ) -> Tuple[bool, Optional[str]]:
        return batch_ingestion_validator.validate_batch_request(
            device=device,
            telemetry_data=telemetry_data,
            image_files=image_files
        )

batch_ingestion_validator_provider = BatchIngestionValidatorProvider()