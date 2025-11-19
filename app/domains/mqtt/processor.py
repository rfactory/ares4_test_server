import logging
import json
import time
import redis
from sqlalchemy.orm import Session
from paho.mqtt.client import Client as MqttClient
from datetime import datetime, timezone

# Security and CRUD imports for server2
from app.core.security import verify_hmac
from app.domains.accounts.crud import user_crud
from app.domains.devices.crud import device_crud
from app.domains.components.crud import supported_component_crud, device_component_instance_crud
from app.domains.hardware.crud import hardware_blueprint_crud
from app.domains.data.crud import telemetry_crud
from app.domains.data.schemas import TelemetryDataCreate

logger = logging.getLogger(__name__)

def _flatten_telemetry_payload(
    payload_dict: dict,
    component_type: str,
    supported_component, # Assuming SupportedComponent model with a .metadata attribute
    state_key: str,
    redis_pipe: redis.client.Pipeline
) -> None:
    """
    Processes and flattens telemetry payload data based on component metadata.
    Updates the Redis pipeline with appropriate HSET commands.
    """
    if supported_component and supported_component.metadata:
        # Assuming supported_component.metadata is a dictionary matching the server1 structure
        # e.g., {"temperature": {"payload_path": "value.temp", "redis_key": "temperature"}}
        metadata = supported_component.metadata
        for metric_name, mapping in metadata.items():
            payload_path = mapping.get("payload_path")
            redis_key = mapping.get("redis_key")
            if payload_path and redis_key:
                value = payload_dict
                for part in payload_path.split('.'):
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None # Path not found, break and set value to None
                        break
                if value is not None:
                    redis_pipe.hset(state_key, redis_key, json.dumps(value))
    else:
        # Fallback: store entire payload under component_type key if no metadata or metadata is empty
        # This will store a JSON string of the entire payload.
        redis_pipe.hset(state_key, component_type, json.dumps(payload_dict))
        logger.warning(f"No metadata found for component_type '{component_type}'. Storing raw payload for {state_key}.")

def handle_telemetry(context: dict, topic: str, payload: dict):
    """
    Handles messages from the 'telemetry/#' topic.
    - Verifies HMAC
    - Validates data integrity
    - Updates Redis cache
    - Saves to database
    """
    db: Session = context["db"]
    redis_client = context["redis_client"]
    mqtt_client: MqttClient = context["mqtt_client"]

    logger.info(f"Processing telemetry message from topic: {topic}")
    
    topic_parts = topic.split('/')
    if len(topic_parts) < 4:
        logger.warning(f"Invalid telemetry topic: {topic}")
        return

    user_email, device_uuid, component_type = topic_parts[1], topic_parts[2], topic_parts[3]

    # 1. HMAC Verification
    received_hmac = payload.pop("hmac", None)
    user = user_crud.get_user_by_email(db, email=user_email)
    if not user or not user.shared_secret:
        logger.warning(f"SECURITY: User {user_email} not found or no shared secret. Cannot verify HMAC.")
        return

    if not verify_hmac(payload, user.shared_secret, received_hmac):
        logger.warning(f"SECURITY: HMAC validation failed for message from {device_uuid}. Message discarded.")
        return

    # 2. Data Integrity and Device Identity Checks
    device = device_crud.get_by_current_uuid(db, current_uuid=device_uuid)
    if not device:
        logger.warning(f"Data-Integrity: Device with UUID {device_uuid} not found. Message discarded.")
        return

    # SECURITY: Verify CPU serial to prevent SD card swapping/cloning attacks
    payload_cpu_serial = payload.get('cpu_serial')
    if not payload_cpu_serial or payload_cpu_serial != device.cpu_serial:
        logger.critical(
            f"SECURITY_ALERT: CPU Serial mismatch for device UUID {device_uuid}! "
            f"DB expects '{device.cpu_serial}' but payload reported '{payload_cpu_serial}'. "
            f"Possible SD card swap attack. Message discarded."
        )
        return

    supported_component = supported_component_crud.get_by_component_type(db, component_type=component_type)
    if not supported_component:
        logger.warning(f"Data-Integrity: Component type '{component_type}' is not supported. Message discarded.")
        return

    component_instance = device_component_instance_crud.get_by_device_id_and_supported_component_id(
        db, device_id=device.id, supported_component_id=supported_component.id
    )
    if not component_instance:
        logger.warning(f"Data-Integrity: Component '{component_type}' is not attached to device {device_uuid}. Message discarded.")
        return

    if not hardware_blueprint_crud.is_component_valid_for_blueprint(
        db, blueprint_id=device.hardware_blueprint_id, supported_component_id=supported_component.id
    ):
        logger.warning(f"Data-Integrity: Component '{component_type}' is not valid for hardware blueprint of device {device_uuid}. Message discarded.")
        return

    # 3. Update Redis Cache
    state_key = f"device_state:{device_uuid}"
    pipe = redis_client.pipeline()
    pipe.hset(state_key, "user_email", user_email)
    pipe.hset(state_key, "device_status", "ONLINE")
    pipe.hset(state_key, "last_seen_at", datetime.now(timezone.utc).isoformat()) # Store last seen timestamp

    _flatten_telemetry_payload(payload, component_type, supported_component, state_key, pipe)

    pipe.execute()

    # 4. Publish updated state
    updated_state = redis_client.hgetall(state_key)
    response_topic = f"client/state/{user_email}/{device_uuid}"
    mqtt_client.publish(response_topic, json.dumps(updated_state))

    # 5. Save to Database
    device.last_seen_at = datetime.now(timezone.utc)
    db.add(device)

    # Create normalized telemetry records
    timestamp = datetime.fromisoformat(payload['timestamp'])
    
    # Get metadata for unit extraction
    metadata = supported_component.metadata if supported_component and supported_component.metadata else {}

    for metric_name_in_payload, value in payload.items():
        if metric_name_in_payload not in ['timestamp', 'hmac', 'cpu_serial']: # Exclude cpu_serial from metrics
            # Try to find the unit from the metadata. The key for metadata is the 'metric_name'
            # For example, if payload contains {'temperature': 25}, and metadata is {'temperature': {'unit': 'C'}}
            # We assume metric_name_in_payload matches a key in the metadata dictionary
            unit = None
            # Check if this metric was flattened and has a defined redis_key and unit in metadata
            for _, mapping in metadata.items():
                if mapping.get("payload_path") == metric_name_in_payload and mapping.get("unit"):
                    unit = mapping.get("unit")
                    break
                # If not using payload_path for direct match, check if metric_name_in_payload is a metric_name in metadata
                elif mapping.get("metric_name") == metric_name_in_payload and mapping.get("unit"):
                    unit = mapping.get("unit")
                    break

            telemetry_record = TelemetryDataCreate(
                device_id=device.id,
                timestamp=timestamp,
                metric_name=f"{component_type}_{metric_name_in_payload}", # Prefix with component_type for uniqueness
                metric_value=float(value),
                unit=unit
            )
            telemetry_crud.create_telemetry_data(db, telemetry_data=telemetry_record)
    
    db.commit()
    logger.info(f"Successfully processed telemetry for {component_type} from {device_uuid}")

def handle_state_request(context: dict, topic: str, payload: dict):
    """
    Handles messages from the 'client/request_state/#' topic.
    - Fetches state from Redis
    - Publishes state back to the client
    """
    logger.info(f"Processing state request from topic: {topic}")
    db: Session = context["db"]
    redis_client = context["redis_client"]
    mqtt_client: MqttClient = context["mqtt_client"]

    topic_parts = topic.split('/')
    if len(topic_parts) < 4:
        logger.warning(f"Invalid state request topic: {topic}")
        return

    user_email, device_uuid = topic_parts[2], topic_parts[3]
    state_key = f"device_state:{device_uuid}"

    try:
        cached_state = redis_client.hgetall(state_key)
        response_payload = json.dumps(cached_state if cached_state else {})
        response_topic = f"client/state/{user_email}/{device_uuid}"
        
        mqtt_client.publish(response_topic, response_payload)
        logger.info(f"Sent state for {device_uuid} to {response_topic}. State: {response_payload}")
    except Exception as e:
        logger.error(f"Failed to handle state request for {device_uuid}: {e}", exc_info=True)

def handle_lwt_message(context: dict, topic: str, payload: dict):
    """
    Handles Last Will and Testament (LWT) messages from the 'device/lwt/status/#' topic.
    - Sets the device status to OFFLINE in Redis.
    - Publishes the updated state to clients.
    """
    db: Session = context["db"]
    redis_client = context["redis_client"]
    mqtt_client: MqttClient = context["mqtt_client"]

    logger.warning(f"Processing LWT message from topic: {topic}")

    topic_parts = topic.split('/')
    if len(topic_parts) < 4:
        logger.error(f"Invalid LWT topic format: {topic}")
        return

    device_uuid = topic_parts[3]
    state_key = f"device_state:{device_uuid}"

    try:
        # Check if device exists in Redis before processing
        if not redis_client.exists(state_key):
            logger.warning(f"Received LWT for unknown or uninitialized device: {device_uuid}. Ignoring.")
            return

        redis_client.hset(state_key, "device_status", "OFFLINE")
        logger.warning(f"Device {device_uuid} has gone offline (LWT). Status updated to OFFLINE.")

        # Publish the updated state to notify clients
        user_email = redis_client.hget(state_key, "user_email")
        if user_email:
            updated_state = redis_client.hgetall(state_key)
            response_topic = f"client/state/{user_email}/{device_uuid}"
            
            # The hgetall method from the redis-py library returns a dictionary where both keys and values are bytes.
            # We need to decode them to strings before serializing to JSON.
            decoded_state = {k.decode('utf-8'): v.decode('utf-8') for k, v in updated_state.items()}
            
            mqtt_client.publish(response_topic, json.dumps(decoded_state))
            logger.info(f"Published 'OFFLINE' state for {device_uuid} to topic {response_topic}.")
        else:
            logger.warning(f"Could not find user_email for device {device_uuid} to publish LWT state update.")

    except Exception as e:
        logger.error(f"Failed to handle LWT message for {device_uuid}: {e}", exc_info=True)

