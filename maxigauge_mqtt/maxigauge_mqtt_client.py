import logging

import paho.mqtt.client as mqtt
import yaml
from threading import Event

from .maxigauge_controller import MaxigaugeController

logger = logging.getLogger(__name__)


class MaxiGaugeMQTTClient:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.topic_base = self.config["topic_base"]
        self.device_name = self.config["device_name"]

        self.user_stop_event = Event()

        self.client = self.connect_mqtt()

        # last will and testament
        self.client.will_set(
            f"{self.topic_base}/{self.device_name}/status",
            "offline",
            qos=1,
            retain=True,
        )

        self.controller = MaxigaugeController(self.config["maxigauge_address"])

    def load_config(self, config_file):
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        return config

    def connect_mqtt(self):
        client = mqtt.Client(
            client_id=self.config["client_id"],
            clean_session=False,
        )
        client.connect(self.config["mqtt_broker"], self.config["mqtt_port"])
        return client

    def main(self):
        logger.info("Starting main loop.")
        try:
            self.client.loop_start()
            self.client.publish(
                f"{self.topic_base}/{self.device_name}/status",
                "online",
                qos=1,
                retain=True,
            )

            while True:
                logger.debug("Reading data.")
                units = self.controller.read_units()
                logger.debug(f"Units: {units}")
                self.client.publish(
                    f"{self.topic_base}/{self.device_name}/units", units
                )

                status, pressure = self.controller.read_pressures()
                for ch, (s, p) in enumerate(zip(status, pressure)):
                    logger.debug(
                        f"Ch: {ch} ... Status: {self.controller.decode_channel_status(s)}, Pressure: {p}"
                    )
                    self.client.publish(
                        f"{self.topic_base}/{self.device_name}/status/{ch}",
                        self.controller.decode_channel_status(s),
                    )
                    self.client.publish(
                        f"{self.topic_base}/{self.device_name}/pressure/{ch}", p
                    )

                # wait for the next interval
                self.user_stop_event.wait(self.config["interval"])
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise e
        finally:
            self.client.publish(
                f"{self.topic_base}/{self.device_name}/status",
                "offline",
                qos=1,
                retain=True,
            )
            self.client.loop_stop()
            self.close()

    def stop(self):
        self.user_stop_event.set()

    def close(self):
        try:
            self.controller.close()
        except:
            pass

        try:
            self.client.disconnect()
        except:
            pass

    def __del__(self):
        self.close()
