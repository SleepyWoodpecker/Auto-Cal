from cli import cli


def main() -> None:
    app = cli.AutoCalCli(
        serial_port="/dev/tty.usbserial-0001", num_readings_per_pressure=10, num_pts=3
    )
    app.run()


if __name__ == "__main__":
    main()
