from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label, ProgressBar, DataTable, Button
from textual.containers import HorizontalGroup, VerticalGroup, Container
from textual.validation import Number
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.message import Message
from textual.widget import Widget
from textual.timer import Timer


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create header and footer"""
        yield Header()
        yield Footer()
        yield FullCalibrationDisplay()

    # custom functions which are to be called should be in the form: action_func_name
    def action_toggle_dark(self) -> None:
        """Toggle appearance of cli"""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


class AverageRawReadingUpdated(Message):
    def __init__(self, pressure: float, raw_reading: float) -> None:
        self.pressure = pressure
        self.raw_reading = raw_reading
        super().__init__()


class TableRowUpdated(Message):
    def __init__(self, pressure: float, raw_reading: float) -> None:
        self.pressure = pressure
        self.raw_reading = raw_reading
        super().__init__()


class FullCalibrationDisplay(HorizontalGroup):
    """The main container for displaying the current readings and the previously calculated readings"""

    # current set of readings + current set of commands
    def compose(self) -> ComposeResult:
        with Container(id="main-app-container"):
            yield CurrentCalibrationDisplay()
            yield PreviousCalculationDisplay()

    def on_average_raw_reading_updated(self, message: AverageRawReadingUpdated) -> None:
        self.query_one(PreviousCalculationDisplay).post_message(
            TableRowUpdated(message.pressure, message.raw_reading)
        )


class PressureUpdated(Message):
    def __init__(self, pressure: float) -> None:
        self.pressure = pressure
        super().__init__()


class CurrentCalibrationDisplay(VerticalGroup):
    """Display the current set of readings + the command prompt"""

    current_pressure: reactive[float] = reactive(-1)

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            yield CurrentCalibrationProgressIndicator().data_bind(
                CurrentCalibrationDisplay.current_pressure
            )
            yield CurrentCalibrationUserInputWidget().data_bind()

    def on_pressure_updated(self, message: PressureUpdated) -> None:
        """Handle pressure updates from child widgets"""
        self.current_pressure = message.pressure

    # def on_average_raw_reading_updated(
    #     self, avg_raw_readings: AverageRawReadingUpdated
    # ) -> None:
    #     """Forward the avg_raw_readings message to the parent"""
    #     print(f"CurrentCalibrationDisplay received message: {avg_raw_readings}")
    #     self.post_message(avg_raw_readings)
    #     print("CurrentCalibrationDisplay forwarded message")


class CurrentCalibrationProgressIndicator(Widget):
    current_pressure: reactive[float] = reactive(-1)
    raw_reading: reactive[float] = reactive(-1)

    progress_timer: Timer
    is_first_load = True

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label(
                f"Reading pressure... {self.current_pressure}", id="pressure-display"
            )
            yield Label("", id="raw-reading")
            yield ProgressBar(total=11)
            yield Button(label="New")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Assign to the reactive variable to trigger the watcher
        print(f"Button pressed! Current raw_reading: {self.raw_reading}")
        self.raw_reading = self.raw_reading + 10
        print(f"New raw_reading value: {self.raw_reading}")

    def watch_current_pressure(self, pressure: float) -> None:
        """Update the label when pressure changes"""
        try:
            label = self.query_one("#pressure-display", Label)
            label.update(f"Reading pressure... {pressure if pressure >= 0 else ''}")
            self.current_pressure = pressure

            # NOTE: After the new pressure is indicated, wait a fixed amount of time for the raw reading to stabilize. Currently, it is a hard coded value of 3 seconds
            if not self.is_first_load:
                self.set_timer(3, lambda: self.query_one(ProgressBar).advance(1))
            else:
                self.is_first_load = False

        except NoMatches:
            pass

    def watch_raw_reading(self, new_reading: float) -> None:
        """Update the screen when a raw reading comes in from serial"""
        print(f"watch_raw_reading called with: {new_reading}")
        try:
            label = self.query_one("#raw-reading", Label)
            label.update(f"{f'Raw reading: {new_reading}' if new_reading >= 0 else ''}")

            self.post_message(
                AverageRawReadingUpdated(self.current_pressure, new_reading)
            )
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
        table.add_columns("Pressure", "Avg Raw Voltage")

    def on_table_row_updated(self, message: TableRowUpdated) -> None:
        table = self.query_one(DataTable)
        table.add_row(message.pressure, message.raw_reading)
