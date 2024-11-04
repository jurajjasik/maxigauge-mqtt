import logging

from maxigauge_mqtt.maxigauge_mqtt_client import MaxiGaugeMQTTClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "config.yaml"

    client = MaxiGaugeMQTTClient(config_file)
    client.main()
