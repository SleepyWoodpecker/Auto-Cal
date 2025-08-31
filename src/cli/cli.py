from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label, ProgressBar, DataTable
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


class CalculateLinearRegressionAction(Message):
    def __init__(self):
        super().__init__()


class TriggerCalibrationMessageAction(Message):
    def __init__(self):
        super().__init__()


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+g", "calibrate", "Calibrate PTs"),
    ]

    def __init__(
        self,
        baud_rate: int,
        num_readings_per_pressure: int,
        serial_port: str,
        num_pts: int,
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.num_pts = num_pts

        # initialize a serial reader class
        self.serial_reader = serial_reader.SerialReader(
            serial_port, baud_rate, 3, num_readings_per_pressure
        )
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create header and footer"""
        yield Header()
        yield Footer()
        yield FullCalibrationDisplay(
            self.num_readings_per_pressure, self.num_pts, self.serial_reader
        )

    def _post_calibration_message(self) -> None:
        self.query_one(PreviousCalculationDisplay).post_message(
            CalculateLinearRegressionAction()
        )

    def action_calibrate(self) -> None:
        """Tell the system to calculate the linear regression"""
        self._post_calibration_message()

    def on_trigger_calibration_message_action(
        self, message: TriggerCalibrationMessageAction
    ) -> None:
        self._post_calibration_message()


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

    def __init__(
        self,
        num_readings_per_pressure: int,
        num_pts: int,
        serial_reader: serial_reader.SerialReader,
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.num_pts = num_pts
        self.serial_reader = serial_reader
        super().__init__()

    # current set of readings + current set of commands
    def compose(self) -> ComposeResult:
        with Container(id="main-app-container"):
            yield CurrentCalibrationDisplay(
                self.num_readings_per_pressure, self.serial_reader
            )
            yield PreviousCalculationDisplay(self.num_pts, self.serial_reader)

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

    def __init__(
        self, num_readings_per_pressure: int, serial_reader: serial_reader.SerialReader
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.serial_reader = serial_reader
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            yield CurrentCalibrationUserInputWidget().data_bind()
            yield CurrentCalibrationProgressIndicator(
                self.num_readings_per_pressure, self.serial_reader
            ).data_bind(CurrentCalibrationDisplay.current_pressure)

    def on_pressure_updated(self, message: PressureUpdated) -> None:
        """Handle pressure updates from child widgets"""
        self.current_pressure = message.pressure

        # reset the progress bar as well
        try:
            self.query_one(ProgressBar).update(progress=0)
        except NoMatches:
            pass


class CurrentCalibrationProgressIndicator(Widget):
    current_pressure: reactive[float] = reactive(-1)
    raw_reading: reactive[float] = reactive(-1)

    progress_timer: Timer
    is_first_load = True

    def __init__(
        self, num_readings_per_pressure: int, serial_reader: serial_reader.SerialReader
    ):
        self.num_readings_per_pressure = num_readings_per_pressure
        self.serial_reader = serial_reader
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label(
                f"Reading pressure... {self.current_pressure}", id="pressure-display"
            )
            yield Label("", id="raw-reading")
            with Middle():
                yield ProgressBar(
                    total=self.num_readings_per_pressure,
                    show_eta=False,
                    show_percentage=False,
                )

    def watch_current_pressure(self, pressure: float) -> None:
        """Update the label when pressure changes"""
        try:
            label = self.query_one("#pressure-display", Label)
            label.update(f"Reading pressure... {pressure if pressure >= 0 else ''}")
            self.current_pressure = pressure

            if not self.is_first_load:
                self.run_worker(
                    self.take_readings_from_serial,
                    exclusive=True,
                    exit_on_error=True,
                    thread=True,
                )
            else:
                self.is_first_load = False

        except NoMatches:
            pass

    # async method to handle the reading of data from serial
    async def take_readings_from_serial(self) -> None:
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
                    self.current_pressure,
                    self.serial_reader.calculate_avg(self.current_pressure),
                )
            )

        return

    def watch_raw_reading(self, new_reading: float) -> None:
        """Update the screen when a raw reading comes in from serial"""
        print(f"watch_raw_reading called with: {new_reading}")
        try:
            label = self.query_one("#raw-reading", Label)
            label.update(f"{f'Raw reading: {new_reading}' if new_reading >= 0 else ''}")

        except NoMatches:
            pass

    def on_mount(self) -> None:
        """Set up timer"""
        self.query_one(ProgressBar).update(progress=0)


class CurrentCalibrationUserInputWidget(VerticalGroup):
    """The widget which accepts user input"""

    BINDINGS = [
        ("escape", "blur", "unfocus input"),
        ("ctrl+g", "calibrate_message", "calibrate PTs"),
    ]

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

    def action_calibrate_message(self) -> None:
        self.post_message(TriggerCalibrationMessageAction())


class PreviousCalculationDisplay(VerticalGroup):
    def __init__(self, num_pts: int, serial_reader: serial_reader.SerialReader) -> None:
        self.num_pts = num_pts
        self.serial_reader = serial_reader
        super().__init__()

    def compose(self) -> ComposeResult:
        with Container(id="previous-display"):
            yield Label("Previous readings")
            yield DataTable()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)

        # create an additional column for each PT there is
        pt_columns = [f"PT {i + 1}" for i in range(self.num_pts)]
        table.add_column("Pressure", key="Pressure")
        for pt in pt_columns:
            table.add_column(pt, key=pt)

    def on_table_row_updated(self, message: TableRowUpdated) -> None:
        table = self.query_one(DataTable)

        # only add rows to the table if the values are valid
        if message.pressure >= 0 and message.pressure >= 0:
            table.add_row(message.pressure, *message.raw_readings)

    def on_calculate_linear_regression_action(
        self, message: CalculateLinearRegressionAction
    ) -> None:
        try:
            table = self.query_one(DataTable)
            self.query_one(Label).update("Calibration factors")
        except NoMatches:
            return

        table.clear()

        # remove the old columns
        table.remove_column("Pressure")
        pt_columns = [f"PT {i + 1}" for i in range(self.num_pts)]
        for pt in pt_columns:
            table.remove_column(pt)

        # add a calibration column to the start
        table.add_column("Calibration Values", key="values")
        table.add_columns(*pt_columns)

        lrs = self.serial_reader.get_all_linear_regressions()

        # add the m values
        slopes = [val[0] for val in lrs.values()]
        table.add_row("m", *slopes)

        intercepts = [val[1] for val in lrs.values()]
        table.add_row("c", *intercepts)
