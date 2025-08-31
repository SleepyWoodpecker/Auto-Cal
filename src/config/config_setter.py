import inquirer
from inquirer import errors as inquirer_errors


def validate_number(answers, current) -> bool:
    try:
        int(current)
        return True
    except ValueError:
        raise inquirer_errors.ValidationError("", reason="Invalid number")


class Config:
    def __init__(self):
        self.questions = [
            inquirer.Text(
                "num_pts",
                message="Number of pts to calibrate",
                validate=validate_number,
            ),
            inquirer.Text(
                "num_readings_per_pt",
                message="Number of readings to take per pt",
                validate=validate_number,
            ),
        ]

    def prompt(self):
        return inquirer.prompt(self.questions, raise_keyboard_interrupt=True)
