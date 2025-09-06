from cli import cli
from config import config_setter
import sys

HV = "High Voltage"
LV = "Low Voltage"


def main() -> None:
    # first get the config params
    config = config_setter.Config(hv=HV, lv=LV)

    answers = None

    try:
        answers = config.prompt()
    except KeyboardInterrupt:
        print("Set-up cancelled, exiting...")
        sys.exit(1)

    if not answers:
        print("No answers provided for set up. Exiting.")
        sys.exit(1)

    if not answers.get("pt_configs", None):
        print("No PTs to calibrate. Exiting.")
        sys.exit(1)

    app = cli.AutoCalCli(
        baud_rate=int(answers["baud_rate"]),
        num_readings_per_pressure=int(answers["num_readings_per_pt"]),
        pt_configs=answers["pt_configs"],
        hv=HV,
        lv=LV,
    )
    app.run()


if __name__ == "__main__":
    main()
