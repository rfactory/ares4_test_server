import logging
import time
import os
import redis
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.config import settings
from app.domains.devices.crud import device_crud
from app.models.objects.device import DeviceStatusEnum 
from app.core.mqtt_publisher import publish_device_status # New MQTT publisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("device_health_checker.log") # Log to file
    ]
)
logger = logging.getLogger(__name__)

def get_redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True # Decode Redis responses to strings
    )

def main():
    logger.info("Device health checker started.")
    redis_client = get_redis_client()

    while True:
        db: Session = SessionLocal()
        try:
            # Get all device_state keys
            device_state_keys = [key for key in redis_client.scan_iter("device_state:*")]

            for key in device_state_keys:
                device_uuid = key.split(':')[1]
                
                cached_state = redis_client.hgetall(key)
                
                device_status = cached_state.get("device_status")
                last_seen_at_str = cached_state.get("last_seen_at")
                user_email = cached_state.get("user_email") # User email is needed for MQTT topic

                if device_status == DeviceStatusEnum.ONLINE.value and last_seen_at_str:
                    try:
                        last_seen_at = datetime.fromisoformat(last_seen_at_str)
                        
                        if last_seen_at.tzinfo is None:
                            last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
                        
                        time_difference = datetime.now(timezone.utc) - last_seen_at

                        if time_difference > timedelta(seconds=settings.DEVICE_TIMEOUT_SECONDS):
                            logger.warning(f"Device {device_uuid} timed out. Last seen {last_seen_at_str}.")
                            
                            # Update status in Redis
                            redis_client.hset(key, "device_status", DeviceStatusEnum.TIMEOUT.value)

                            # Update status in DB
                            db_device = device_crud.get_by_current_uuid(db, current_uuid=device_uuid)
                            if db_device and db_device.status != DeviceStatusEnum.TIMEOUT:
                                db_device.status = DeviceStatusEnum.TIMEOUT
                                db.add(db_device)
                                db.commit()
                                logger.info(f"Updated DB status for {device_uuid} to {DeviceStatusEnum.TIMEOUT.value}.")

                                # Publish updated state via MQTT
                                if user_email:
                                    publish_device_status(user_email=user_email, device_uuid=device_uuid, status_payload={"status": DeviceStatusEnum.TIMEOUT.value})
                                    logger.info(f"Published 'TIMEOUT' state for {device_uuid} via MQTT.")
                                else:
                                    logger.warning(f"Could not find user_email for device {device_uuid} to publish TIMEOUT state update.")
                            elif not db_device:
                                logger.error(f"Timed out device {device_uuid} not found in DB.")
                            
                        
                    except ValueError as ve:
                        logger.error(f"Invalid last_seen_at format for {device_uuid}: {last_seen_at_str}. Error: {ve}")
                
            db.close() 

        except Exception as e:
            logger.error(f"Error in device health checker loop: {e}", exc_info=True)
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

        logger.info(f"Next check in {settings.DEVICE_HEALTH_CHECK_INTERVAL_SECONDS} seconds.")
        time.sleep(settings.DEVICE_HEALTH_CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()