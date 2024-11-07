# maxigauge-mqtt

This is a simple python script that reads the data from a TPG 366 Maxigauge and publishes it to an MQTT broker. The script is designed to run as a service on a Raspberry Pi.

## Dependencies

- [paho-mqtt](https://pypi.org/project/paho-mqtt/)
- [pyvisa](https://pyvisa.readthedocs.io/en/latest/)

## Configuration

The script is configured using a YAML file. The default configuration file is `config.yaml`. The configuration file should look like this:

```yaml
client_id: maxigauge-ce583f23-98c6-4353-84c8-e14f5830bbaf
topic_base: "pressure"
device_name: "MaxiGauge"
mqtt_broker: "localhost"
mqtt_port: 1883
mqtt_connection_timeout: 60

maxigauge_address: "TCPIP::192.168.0.101::8000::SOCKET"
interval: 1.0  # seconds
```

### Configuration Options

- `client_id`: The MQTT client ID.
- `topic_base`: The base topic to publish the data to.
- `device_name`: The name of the device.
- `mqtt_broker`: The hostname of the MQTT broker.
- `mqtt_port`: The port of the MQTT broker.
- `mqtt_connection_timeout`: The timeout for the MQTT connection.
- `maxigauge_address`: The VISA address of the Maxigauge.
- `interval`: The interval between readings.

## MQTT Message Structure

The script publishes the following messages to the MQTT broker:

- `<topic_base>/<device_name>/status`: The status of the Maxigauge with json payload, e.g. `{"value": "ONLINE"}`

- `<topic_base>/<device_name>/readbacks`: The readbacks of the Maxigauge with json payload, e.g. `{"units": "mbar", "sensors": [{"name": "FOREPUMP", "status": "No Sensor", "value": 0.0}, {"name": "CHAMBER_", "status": "No Sensor", "value": 0.0}, {"name": "________", "status": "No Sensor", "value": 0.0}, {"name": "________", "status": "No Sensor", "value": 0.0}, {"name": "________", "status": "No Sensor", "value": 0.0}, {"name": "________", "status": "No Sensor", "value": 0.0}]}`

## Installation of the maxigauge-mqtt service

Clone the repository:

```bash
git clone https://github.com/jurajjasik/maxigauge-mqtt
```

Modify the configuration file of the QSource3-MQTT service:

```bash
nano maxigauge-mqtt/config.yaml
```

Test the script:

```bash
python3 maxigauge-mqtt/maxigauge_mqtt_main.py maxigauge-mqtt/config.yaml
```

Inspect the MQTT messages using the Mosquitto MQTT client:

```bash
mosquitto_sub -F '@Y-@m-@dT@H:@M:@S@z : %t : %J' -t "pressure/MaxiGauge/#" -v -h localhost -p 1883
```

Install the service:

```bash
sudo cp maxigauge-mqtt/maxigauge-mqtt.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/maxigauge-mqtt.service
sudo systemctl daemon-reload
sudo systemctl enable maxigauge-mqtt
sudo systemctl start maxigauge-mqtt
```

The service is now running and will start automatically on boot. To check the status of the service, run:

```bash
sudo systemctl status maxigauge-mqtt
```

To view the last 30 lines of the log file, run:

```bash
journalctl -u maxigauge-mqtt --no-pager --no-hostname --lines 30
```

To stop the service, run:

```bash
sudo systemctl stop maxigauge-mqtt
```

To disable the service from starting on boot, run:

```bash
sudo systemctl disable maxigauge-mqtt
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
