from serial import Serial
import numpy as np
import threading
from cal import cal


class SerialReader:
    def __init__(
        self,
        serial_port: str,
        baud_rate: int,
        num_sensors: int,
        num_readings_per_pt: int,
        name: str,
        timeout: int = 2,
    ):
        self.serial = Serial(serial_port, baudrate=baud_rate, timeout=timeout)
        self.readings = {i: [] for i in range(num_sensors)}
        self.num_sensors = num_sensors
        self.num_readings_per_pt = num_readings_per_pt
        self.serial_lock = threading.Lock()
        self.all_avgs = {i: [] for i in range(num_sensors)}
        self.name = name
        # id is different from name because ID must not have spaces
        self.id = "-".join(name.split(" "))

    def read_from_serial(self) -> None:
        """take a reading from serial, and place it into the readings dict"""
        # clear the current readings first
        with self.serial_lock:
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
            raise ValueError(
                f"Expected {self.num_sensors} readings, but received {len(readings)} | readings: {readings}"
            )

        # add the reading to the dict
        for pt_no, reading in enumerate(readings):
            self.readings[pt_no].append(np.float64(reading))

    def calculate_avg(self, current_pressure: float) -> list[float]:
        """calculate the average reading for the current set of values and clear the reading history"""
        avg_readings = []
        for pt_no, readings in self.readings.items():
            avg_for_pt = np.mean(np.array(readings)).item()
            avg_readings.append(avg_for_pt)
            self.all_avgs[pt_no].append((current_pressure, avg_for_pt))

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

    def get_all_linear_regressions(self) -> dict[int, tuple[float, float]]:
        """returns data in format pt: (m, c)"""
        linear_regressions = {}
        for pt, pressure_value_pair in self.all_avgs.items():
            pressures = []
            avg_readings = []
            for pressure, avg_reading in pressure_value_pair:
                pressures.append(pressure)
                avg_readings.append(avg_reading)

            linear_regressions[pt] = cal.calculate_linear_regression(
                pressures, avg_readings
            )

        return linear_regressions

    def get_pt_name(self) -> str:
        return self.name

    def get_num_pts(self) -> int:
        return self.num_sensors

    def get_pt_id(self) -> str:
        return self.id
