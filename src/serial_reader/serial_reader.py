from serial import Serial
import numpy as np


class SerialReader:
    def __init__(
        self, serial_port: str, baud_rate: int, num_sensors: int, timeout: int = 2
    ):
        self.serial = Serial(serial_port, baudrate=baud_rate, timeout=timeout)
        self.readings = {i: [] for i in range(num_sensors)}
        self.num_sensors = num_sensors

    def read_from_serial(self) -> None:
        """take a reading from serial, and place it into the readings dict"""
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
            self.readings[pt_no].append(reading)

    def calculate_avg(self) -> dict[int, float]:
        """calculate the average reading for the current set of values and clear the reading history"""
        avg_dict = {}
        for pt_no, readings in self.readings.items():
            avg_dict[pt_no] = np.mean(np.array(readings))
            self.readings[pt_no] = []

        return avg_dict
