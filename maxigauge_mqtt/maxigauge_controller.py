import pyvisa
import logging

logger = logging.getLogger(__name__)


class MaxigaugeController:
    ACK = "\x06"
    NAK = "\x15"
    ENQ = b"\x05"

    def __init__(self, address):
        self.address = address
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(self.address)

        self.instrument.write_termination = "\r"
        self.instrument.read_termination = "\r\n"

    def send_command(self, mnemonic):
        """
        Send a command to the instrument and wait for an ACK or NAK response.
        """
        logger.debug(f"Sending command: {mnemonic}")
        self.instrument.write(mnemonic)
        response = self.instrument.read()
        if response == self.ACK:
            logger.debug("Received ACK response.")
            return True  # Command was successful
        else:
            logger.debug("ACK response not received.")
            return False  # Command failed

    def request_data(self):
        """
        Request data transmission from the instrument using <ENQ>.
        """
        self.instrument.write_raw(self.ENQ)
        response = self.instrument.read()
        logger.debug(f"Received response: {response}")
        return response

    def close(self):
        try:
            self.instrument.close()
        except:
            pass

        try:
            self.rm.close()
        except:
            pass

    def __del__(self):
        self.close()

    def read_pressures(self):
        """
        Read pressures from the instrument.
        """
        mnemonic = "PRX"
        if self.send_command(mnemonic):
            response = self.request_data()
            status, pressure = self.parse_prx_response(response)
            return status, pressure
        else:
            return None

    def parse_prx_response(self, response):
        """
        Parse the PRX response from the instrument.

        PRX has format:
        status1, pressure1, status2, pressure2, ...
        """
        response = response.strip()
        logger.debug(f"Parsing response: {response}")

        status = []
        pressure = []
        response = response.split(",")
        for i in range(0, len(response), 2):
            status.append(response[i])

            # Check if the pressure is a valid number
            try:
                pressure.append(float(response[i + 1]))
            except ValueError:
                pressure.append(float("nan"))

        return status, pressure

    def decode_channel_status(self, status):
        """
        Decode the status of a channel.
        """
        if status == "0":
            return "OK"
        elif status == "1":
            return "Underrange"
        elif status == "2":
            return "Overrange"
        elif status == "3":
            return "Sensor Error"
        elif status == "4":
            return "Sensor Off"
        elif status == "5":
            return "No Sensor"
        elif status == "6":
            return "Identification Error"
        else:
            return "Unknown Status"

    def read_units(self):
        """
        Read the units of the instrument.
        """
        mnemonic = "UNI"
        if self.send_command(mnemonic):
            response = self.request_data()
            return self.decode_units(response)
        else:
            return None

    def decode_units(self, response):
        """
        Decode the units from the response.
        """
        response = response.strip()
        logger.debug(f"Decoding units: {response}")

        if response == "0":
            return "mbar"
        elif response == "1":
            return "Torr"
        elif response == "2":
            return "Pa"
        elif response == "3":
            return "Micron"
        elif response == "4":
            return "hPascal"
        elif response == "5":
            return "Volt"
        else:
            return "Unknown Units"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    )

    controller = MaxigaugeController("TCPIP::192.168.1.101::8000::SOCKET")

    units = controller.read_units()
    print(f"Units: {units}")

    status, pressure = controller.read_pressures()
    for ch, (s, p) in enumerate(zip(status, pressure)):
        print(
            f"Ch: {ch} ... Status: {controller.decode_channel_status(s)}, Pressure: {p}"
        )

    controller.close()
