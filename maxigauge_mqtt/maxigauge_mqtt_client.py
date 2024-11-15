import json
import logging
from threading import Event
import time

import paho.mqtt.client as mqtt
import yaml

from .maxigauge_controller import MaxigaugeController

logger = logging.getLogger(__name__)


class MaxiGaugeMQTTClient:
    STATUS_PAYLOAD_ONLINE = json.dumps({"value": "online"})
    STATUS_PAYLOAD_OFFLINE = json.dumps({"value": "offline"})

    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.topic_base = self.config["topic_base"]
        self.device_name = self.config["device_name"]

        self.user_stop_event = Event()

        self.client = self.connect_mqtt()

        # last will and testament
        self.client.will_set(
            f"{self.topic_base}/{self.device_name}/status",
            self.STATUS_PAYLOAD_OFFLINE,
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
                self.STATUS_PAYLOAD_ONLINE,
                qos=1,
                retain=True,
            )

            while True:
                logger.debug("Reading data.")
                units = self.controller.read_units()
                names = self.controller.read_channel_names()
                status, pressure = self.controller.read_pressures()
                timestamp = time.time()

                payload = {
                    "timestamp": timestamp,
                    "units": units,
                    "sensors": [
                        {
                            "name": n,
                            "status": self.controller.decode_channel_status(s),
                            "value": p,
                        }
                        for n, s, p in zip(names, status, pressure)
                    ],
                }

                # convert payload to json
                payload = json.dumps(payload)

                logger.info(f"Publishing payload: {payload}")

                # publish payload
                self.client.publish(
                    f"{self.topic_base}/{self.device_name}/readbacks",
                    payload,
                    qos=1,
                )

                # wait for the next interval
                self.user_stop_event.wait(self.config["interval"])
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise e
        finally:
            self.client.publish(
                f"{self.topic_base}/{self.device_name}/status",
                self.STATUS_PAYLOAD_OFFLINE,
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
