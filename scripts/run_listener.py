import logging
import sys
import os

# Add the project root to the Python path to allow imports from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.domains.mqtt.listener import MqttListener
from app.core.config import Settings

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """Initializes and runs the MQTT listener."""
    logger = logging.getLogger(__name__)
    logger.info("Starting MQTT listener script...")

    listener = None
    try:
        app_settings = Settings()
        listener = MqttListener(app_settings)
        listener.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down listener script.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if listener:
            listener.stop()
        logger.info("MQTT listener script has shut down.")

if __name__ == "__main__":
    main()
