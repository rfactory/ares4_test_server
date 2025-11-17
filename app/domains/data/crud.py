from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime # datetime 임포트 추가

from app.models.events_logs.telemetry_data import TelemetryData as DBTelemetryData
from app.models.events_logs.telemetry_metadata import TelemetryMetadata as DBTelemetryMetadata
from app.domains.data.schemas import TelemetryDataCreate, TelemetryDataUpdate, TelemetryMetadataCreate

class CRUDTelemetryData:
    def create_telemetry_data(self, db: Session, telemetry_data: TelemetryDataCreate) -> DBTelemetryData:
        db_telemetry = DBTelemetryData(
            device_id=telemetry_data.device_id,
            timestamp=telemetry_data.timestamp,
            metric_name=telemetry_data.metric_name,
            metric_value=telemetry_data.metric_value,
            unit=telemetry_data.unit
        )
        db.add(db_telemetry)
        db.flush() # Flush to get db_telemetry.id for metadata

        if telemetry_data.metadata_items:
            for meta_item in telemetry_data.metadata_items:
                db_metadata = DBTelemetryMetadata(
                    telemetry_data_id=db_telemetry.id,
                    meta_key=meta_item.meta_key,
                    meta_value=meta_item.meta_value,
                    meta_value_type=meta_item.meta_value_type,
                    description=meta_item.description
                )
                db.add(db_metadata)
        
        db.commit()
        db.refresh(db_telemetry)
        return db_telemetry

    def get_telemetry_data(self, db: Session, telemetry_data_id: int) -> Optional[DBTelemetryData]:
        return db.query(DBTelemetryData).options(
            joinedload(DBTelemetryData.metadata_items),
            joinedload(DBTelemetryData.device)
        ).filter(DBTelemetryData.id == telemetry_data_id).first()

    def get_multiple_telemetry_data(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        device_id: Optional[int] = None,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[DBTelemetryData]:
        query = db.query(DBTelemetryData).options(
            joinedload(DBTelemetryData.metadata_items),
            joinedload(DBTelemetryData.device)
        )
        if device_id:
            query = query.filter(DBTelemetryData.device_id == device_id)
        if metric_name:
            query = query.filter(DBTelemetryData.metric_name == metric_name)
        if start_time:
            query = query.filter(DBTelemetryData.timestamp >= start_time)
        if end_time:
            query = query.filter(DBTelemetryData.timestamp <= end_time)
        
        return query.offset(skip).limit(limit).all()

    def update_telemetry_data(
        self, db: Session, telemetry_data_id: int, telemetry_data_update: TelemetryDataUpdate
    ) -> Optional[DBTelemetryData]:
        db_telemetry = db.query(DBTelemetryData).filter(DBTelemetryData.id == telemetry_data_id).first()
        if not db_telemetry:
            return None
        
        update_data = telemetry_data_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_telemetry, key, value)
        
        db.add(db_telemetry)
        db.commit()
        db.refresh(db_telemetry)
        return db_telemetry

    def delete_telemetry_data(self, db: Session, telemetry_data_id: int) -> Optional[DBTelemetryData]:
        db_telemetry = db.query(DBTelemetryData).filter(DBTelemetryData.id == telemetry_data_id).first()
        if not db_telemetry:
            return None
        
        db.delete(db_telemetry)
        db.commit()
        return db_telemetry

telemetry_crud = CRUDTelemetryData()
