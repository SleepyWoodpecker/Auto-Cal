import inquirer, serial
from inquirer import errors as inquirer_errors
from serial.tools import list_ports


def validate_number(answers, current) -> bool:
    try:
        int(current)
        return True
    except ValueError:
        raise inquirer_errors.ValidationError("", reason="Invalid number")


def validate_port(answers, current) -> bool:
    """Check that the selected port is open"""
    try:
        ser = serial.Serial(current, int(answers["baud_rate"]), timeout=1)
        ser.close()
        return True
    except serial.SerialException:
        raise inquirer_errors.ValidationError(
            "", reason=f"{current} is currently in use"
        )


class Config:
    def __init__(self):
        self.questions = [
            inquirer.Text(
                "baud_rate",
                message="Controller baud rate",
                validate=validate_number,
                default=115200,
            ),
            inquirer.List(
                "serial_port",
                message="Serial port to read from",
                choices=[p.device for p in list_ports.comports()],
            ),
            inquirer.Text(
                "num_pts",
                message="Number of pts to calibrate",
                validate=validate_number,
            ),
            inquirer.Text(
                "num_readings_per_pt",
                message="Number of readings to take per pt",
                validate=validate_number,
                default=10,
            ),
        ]

    def prompt(self):
        return inquirer.prompt(self.questions, raise_keyboard_interrupt=True)
