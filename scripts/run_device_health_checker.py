import logging
import time
import redis
from datetime import datetime, timedelta, timezone
import requests 
import json
import uuid # Import uuid

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.config import settings
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider # NEW
from app.models.objects.device import DeviceStatusEnum
from app.domains.inter_domain.device_log.device_log_command_provider import device_log_command_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("device_health_checker.log")
    ]
)
logger = logging.getLogger(__name__)

# New function to call the internal API
def publish_via_internal_api(topic: str, command: dict):
    """
    Calls the internal API to dispatch an MQTT command.
    """
    try:
        url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/api/v1/internal/dispatch-command"
        payload = {"topic": topic, "command": command}
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status() # Raise an exception for bad status codes
        logger.info(f"Successfully requested command dispatch via internal API for topic: {topic}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call internal API to dispatch command for topic {topic}: {e}", exc_info=True)


def get_redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )

def main():
    logger.info("Device health checker started.")
    redis_client = get_redis_client()

    while True:
        db: Session = SessionLocal()
        try:
            device_state_keys = [key for key in redis_client.scan_iter("device_state:*")]

            for key in device_state_keys:
                device_uuid_str = key.split(':')[1]
                device_uuid = uuid.UUID(device_uuid_str)
                
                cached_state = redis_client.hgetall(key)
                
                device_status = cached_state.get("device_status")
                last_seen_at_str = cached_state.get("last_seen_at")
                user_email = cached_state.get("user_email")

                if device_status == DeviceStatusEnum.ONLINE.value and last_seen_at_str:
                    try:
                        last_seen_at = datetime.fromisoformat(last_seen_at_str)
                        
                        if last_seen_at.tzinfo is None:
                            last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
                        
                        time_difference = datetime.now(timezone.utc) - last_seen_at

                        if time_difference > timedelta(seconds=settings.DEVICE_TIMEOUT_SECONDS):
                            logger.warning(f"Device {device_uuid_str} timed out. Last seen {last_seen_at_str}.")
                            
                            # Update status in Redis
                            redis_client.hset(key, "device_status", DeviceStatusEnum.TIMEOUT.value)

                            db_device = device_management_query_provider.get_device_by_uuid(db, current_uuid=device_uuid) # UPDATED
                            if db_device and db_device.status != DeviceStatusEnum.TIMEOUT:
                                db_device.status = DeviceStatusEnum.TIMEOUT
                                db.add(db_device)

                                # Log the TIMEOUT event to device_log table
                                device_log_command_provider.create_device_log(
                                    db=db,
                                    device_id=db_device.id,
                                    log_level="WARNING",
                                    description=f"Device timed out. Last seen at {last_seen_at_str}."
                                )
                                
                                db.commit()
                                logger.info(f"Updated DB status for {device_uuid_str} to {DeviceStatusEnum.TIMEOUT.value} and created device log.")

                                # Publish updated state via internal API
                                if user_email:
                                    topic = f"users/{user_email}/devices/{device_uuid_str}/status"
                                    payload = {"status": DeviceStatusEnum.TIMEOUT.value}
                                    publish_via_internal_api(topic=topic, command=payload)
                                else:
                                    logger.warning(f"Could not find user_email for device {device_uuid_str} to publish TIMEOUT state update.")
                            elif not db_device:
                                logger.error(f"Timed out device {device_uuid_str} not found in DB.")
                            
                    except ValueError as ve:
                        logger.error(f"Invalid last_seen_at format for {device_uuid_str}: {last_seen_at_str}. Error: {ve}")
            
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