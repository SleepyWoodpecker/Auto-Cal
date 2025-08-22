import os
from PyInquirer import prompt
from typing import TypedDict


class UserInput(TypedDict):
    num_pts: int
    calibration_output_folder: str


def get_user_input() -> UserInput:
    """
    get user arguments required for auto-cal to run:
        1. number of pts
        2. output file for calibrations
    """

    questions = []

    questions.append(
        {
            "type": "input",
            "name": "num_pts",
            "message": "Number of pts you wish to calibrate:",
            "validate": lambda val: val.isdigit() or "Please enter a valid integer",
        }
    )

    def validate_folder(val: str) -> bool | str:
        try:
            os.makedirs(val, exist_ok=True)
            return True
        except Exception:
            return "Failed to create output file, please enter another file name"

    questions.append(
        {
            "type": "input",
            "name": "calibration_output_folder",
            "message": "Output folder for calibrations: ",
            "default": "pt_calibrations",
            "validate": validate_folder,
        }
    )

    answers = prompt(questions=questions)

    return answers
