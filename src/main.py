from cli import cli


def main() -> None:
    app = cli.AutoCalCli(serial_port="/dev/tty", num_readings_per_pressure=10)
    app.run()


if __name__ == "__main__":
    main()
