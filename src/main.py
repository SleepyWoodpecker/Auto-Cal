from cli import cli
from config import config_setter
import sys


def main() -> None:
    # first get the config params
    config = config_setter.Config()

    answers = None

    try:
        answers = config.prompt()
    except KeyboardInterrupt:
        print("Set-up cancelled exiting...")
        sys.exit(1)

    if not answers:
        sys.exit(1)

    app = cli.AutoCalCli(
        serial_port="/dev/tty.usbserial-0001",
        num_readings_per_pressure=int(answers["num_readings_per_pt"]),
        num_pts=int(answers["num_pts"]),
    )
    app.run()


if __name__ == "__main__":
    main()
