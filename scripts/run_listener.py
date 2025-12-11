import logging
import sys
import os
import redis
import asyncio

# Add the project root to the Python path to allow imports from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import get_settings
from app.database import SessionLocal
from app.domains.services.mqtt_gateway.managers.mqtt_listener_manager import MqttListenerManager
from app.domains.services.mqtt_gateway.services.mqtt_message_router import MqttMessageRouter
from app.domains.inter_domain.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy_provider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Initializes and runs the new MQTT listener components asynchronously."""
    logger.info("Starting MQTT listener application...")
    
    manager = None
    shutdown_event = asyncio.Event()

    try:
        settings = get_settings()
        
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

        logger.info("Assembling listener components...")
        router = MqttMessageRouter(
            db_session_factory=SessionLocal, 
            redis_client=redis_client
        )

        manager = MqttListenerManager(
            settings=settings, 
            client_id=settings.MQTT_LISTENER_CLIENT_ID
        )

        logger.info("Acquiring certificate for listener from Vault...")
        with SessionLocal() as db:
            cert_data = server_certificate_acquisition_policy_provider.acquire_valid_server_certificate(
                db=db,
                current_cert_data=None
            )
            db.commit()
        
        manager.set_certificate_data(cert_data)

        await manager.connect(on_message_callback=router.handle_message)
        
        logger.info("MQTT listener is running. Waiting for shutdown signal...")
        await shutdown_event.wait()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down listener.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the listener application: {e}", exc_info=True)
    finally:
        if manager:
            await manager.disconnect()
        logger.info("MQTT listener application has shut down.")

if __name__ == "__main__":
    asyncio.run(main())
