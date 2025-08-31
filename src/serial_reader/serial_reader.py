from serial import Serial
import numpy as np


class SerialReader:
    def __init__(
        self,
        serial_port: str,
        baud_rate: int,
        num_sensors: int,
        num_readings_per_pt: int,
        timeout: int = 2,
    ):
        self.serial = Serial(serial_port, baudrate=baud_rate, timeout=timeout)
        self.readings = {i: [] for i in range(num_sensors)}
        self.num_sensors = num_sensors
        self.num_readings_per_pt = num_readings_per_pt

    def read_from_serial(self) -> None:
        """take a reading from serial, and place it into the readings dict"""
        # clear the current readings first
        self.serial.reset_input_buffer()

        line = None
        try:
            line = self.serial.readline().decode().strip()
        except UnicodeDecodeError:
            print("Error decoding current sequence, continuing...")
            return

        if not line:
            return

        # based on the current format, the data is coming in the format:
        # pt1, pt2, pt3...
        readings = line.split(", ")
        if len(readings) != self.num_sensors:
            print(
                f"Expected {self.num_sensors} readings, but received {len(readings)} readings"
            )
            raise ValueError("Incorrect number of pts and sensor readings obtained")

        # add the reading to the dict
        for pt_no, reading in enumerate(readings):
            self.readings[pt_no].append(np.float64(reading))

    def calculate_avg(self) -> list[float]:
        """calculate the average reading for the current set of values and clear the reading history"""
        avg_readings = []
        for pt_no, readings in self.readings.items():
            avg_readings.append(np.mean(np.array(readings)).item())
            self.readings[pt_no] = []

        return avg_readings

    def ready_for_avg(self) -> bool:
        """crudely check for"""
        if len(self.readings) <= 0:
            return False

        for reding_set in self.readings.values():
            if len(reding_set) != self.num_readings_per_pt:
                return False

        return True


if __name__ == "__main__":
    serial = SerialReader(
        serial_port="/dev/tty.usbserial-0001",
        baud_rate=115200,
        num_sensors=3,
        num_readings_per_pt=10,
    )

    for _ in range(10):
        serial.read_from_serial()

    if serial.ready_for_avg():
        print("We are ready!")
        print(serial.calculate_avg())
