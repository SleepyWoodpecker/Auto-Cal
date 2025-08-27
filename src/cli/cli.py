from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label, ProgressBar, DataTable, Button
from textual.containers import (
    HorizontalGroup,
    VerticalGroup,
    Container,
    Middle,
)
from textual.validation import Number
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.message import Message
from textual.widget import Widget
from textual.timer import Timer

from serial_reader import serial_reader


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self, num_readings_per_pressure: int, serial_port: str):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.serial_port = serial_port
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create header and footer"""
        yield Header()
        yield Footer()
        yield FullCalibrationDisplay(self.num_readings_per_pressure, self.serial_port)

    # custom functions which are to be called should be in the form: action_func_name
    def action_toggle_dark(self) -> None:
        """Toggle appearance of cli"""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


class AverageRawReadingUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float]) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        super().__init__()


class TableRowUpdated(Message):
    def __init__(self, pressure: float, raw_readings: list[float]) -> None:
        self.pressure = pressure
        self.raw_readings = raw_readings
        super().__init__()


class FullCalibrationDisplay(HorizontalGroup):
    """The main container for displaying the current readings and the previously calculated readings"""

    def __init__(self, num_readings_per_pressure: int, serial_port: str):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.serial_port = serial_port
        super().__init__()

    # current set of readings + current set of commands
    def compose(self) -> ComposeResult:
        with Container(id="main-app-container"):
            yield CurrentCalibrationDisplay(
                self.num_readings_per_pressure, self.serial_port
            )
            yield PreviousCalculationDisplay()

    def on_average_raw_reading_updated(self, message: AverageRawReadingUpdated) -> None:
        self.query_one(PreviousCalculationDisplay).post_message(
            TableRowUpdated(message.pressure, message.raw_readings)
        )


class PressureUpdated(Message):
    def __init__(self, pressure: float) -> None:
        self.pressure = pressure
        super().__init__()


class CurrentCalibrationDisplay(VerticalGroup):
    """Display the current set of readings + the command prompt"""

    current_pressure: reactive[float] = reactive(-1)

    def __init__(self, num_readings_per_pressure: int, serial_port: str):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.serial_port = serial_port
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            yield CurrentCalibrationUserInputWidget().data_bind()
            yield CurrentCalibrationProgressIndicator(
                self.num_readings_per_pressure, self.serial_port
            ).data_bind(CurrentCalibrationDisplay.current_pressure)

    def on_pressure_updated(self, message: PressureUpdated) -> None:
        """Handle pressure updates from child widgets"""
        self.current_pressure = message.pressure


class CurrentCalibrationProgressIndicator(Widget):
    current_pressure: reactive[float] = reactive(-1)
    raw_reading: reactive[float] = reactive(-1)

    progress_timer: Timer
    is_first_load = True

    def __init__(self, num_readings_per_pressure: int, serial_port: str):
        # initialize a serial reader class
        self.serial_reader = serial_reader.SerialReader(
            serial_port, 115_200, 3, num_readings_per_pressure
        )

        self.num_readings_per_pressure = num_readings_per_pressure
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label(
                f"Reading pressure... {self.current_pressure}", id="pressure-display"
            )
            yield Label("", id="raw-reading")
            with Middle():
                yield ProgressBar(
                    total=self.num_readings_per_pressure + 1,
                    show_eta=False,
                    show_percentage=False,
                )

    def watch_current_pressure(self, pressure: float) -> None:
        """Update the label when pressure changes"""
        try:
            label = self.query_one("#pressure-display", Label)
            label.update(f"Reading pressure... {pressure if pressure >= 0 else ''}")
            self.current_pressure = pressure

            # NOTE: After the new pressure is indicated, wait a fixed amount of time for the raw reading to stabilize. Currently, it is a hard coded value of 3 seconds
            if not self.is_first_load:
                self.run_worker(
                    self.take_readings_from_serial, exclusive=True, exit_on_error=True
                )
            else:
                self.is_first_load = False

        except NoMatches:
            pass

    # async method to handle the reading of data from serial
    async def take_readings_from_serial(self) -> None:
        # serial.read
        for _ in range(self.num_readings_per_pressure):
            self.serial_reader.read_from_serial()

            # progress the bar after taking one reading
            try:
                self.query_one(ProgressBar).advance(1)
            except NoMatches:
                pass

        # after completing the readings, calculate the average values
        if self.serial_reader.ready_for_avg():
            self.post_message(
                AverageRawReadingUpdated(
                    self.current_pressure, self.serial_reader.calculate_avg()
                )
            )

    def watch_raw_reading(self, new_reading: float) -> None:
        """Update the screen when a raw reading comes in from serial"""
        print(f"watch_raw_reading called with: {new_reading}")
        try:
            label = self.query_one("#raw-reading", Label)
            label.update(f"{f'Raw reading: {new_reading}' if new_reading >= 0 else ''}")

            print("Message posted!")

            self.query_one(ProgressBar).advance(1)

        except NoMatches:
            pass

    def on_mount(self) -> None:
        """Set up timer"""

        # NOTE: 11 is an arbitrary value, 1 for setup, another 10 assuming that the average of 10 readings is needed. Need to ensure that this eventually becomes a dynamic value
        self.progress_timer = self.set_interval(0 / 11, None, pause=True)


class CurrentCalibrationUserInputWidget(VerticalGroup):
    """The widget which accepts user input"""

    BINDINGS = [("escape", "blur", "unfocus input")]

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-input-container"):
            yield Label("Current pressure", id="current-pressure-label")
            yield Input(
                id="current-pressure-input",
                validate_on=["submitted"],
                validators=[Number()],
            )
            yield Label("", id="error-message")

    @on(Input.Submitted)
    def accept_user_input(self, event: Input.Submitted):
        input_widget = self.query_one("#current-pressure-input", Input)
        if event.validation_result:
            if event.validation_result.is_valid:
                self.set_error_label("")
                try:
                    pressure_value = float(input_widget.value)
                    self.post_message(PressureUpdated(pressure_value))
                except ValueError:
                    self.set_error_label("Invalid number format!")
            else:
                self.set_error_label("Pressure should be a number!")

        input_widget.value = ""

    def set_error_label(self, error_value: str) -> None:
        error_label = self.query_one("#error-message", Label)
        error_label.update(error_value)

    def on_mount(self) -> None:
        self.call_after_refresh(lambda: self.screen.set_focus(None))

    def action_blur(self) -> None:
        self.screen.set_focus(None)
        self.set_error_label("")
        input_widget = self.query_one("#current-pressure-input", Input)
        input_widget.remove_class("-invalid")


class PreviousCalculationDisplay(VerticalGroup):
    def compose(self) -> ComposeResult:
        with Container(id="previous-display"):
            yield Label("Previous readings")
            yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Pressure", "Avg Voltage")

    def on_table_row_updated(self, message: TableRowUpdated) -> None:
        table = self.query_one(DataTable)

        # only add rows to the table if the values are valid
        if message.pressure >= 0 and message.pressure >= 0:
            table.add_row(message.pressure, *message.raw_readings)
