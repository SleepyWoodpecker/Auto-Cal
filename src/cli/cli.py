from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.containers import HorizontalGroup, VerticalGroup, Container
from textual.validation import Number
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.message import Message
from textual.widget import Widget


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


class FullCalibrationDisplay(HorizontalGroup):
    """The main container for displaying the current readings and the previously calculated readings"""

    # current set of readings + current set of commands
    def compose(self) -> ComposeResult:
        with Container(id="main-app-container"):
            yield CurrentCalibrationDisplay()
            yield PreviousCalculationDisplay()

    # previously calculated set of readings


class PressureUpdated(Message):
    def __init__(self, pressure: float) -> None:
        self.pressure = pressure
        super().__init__()


class CurrentCalibrationDisplay(VerticalGroup):
    """Display the current set of readings + the command prompt"""

    current_pressure: reactive[float] = reactive(-1)

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            # Fix 1: Correct data_bind syntax
            yield CurrentCalibrationProgressIndicator().data_bind(
                CurrentCalibrationDisplay.current_pressure
            )
            yield CurrentCalibrationUserInputWidget().data_bind()

    def on_pressure_updated(self, message: PressureUpdated) -> None:
        """Handle pressure updates from child widgets"""
        print(f"I have a amessage {message.pressure}")
        self.current_pressure = message.pressure


class CurrentCalibrationProgressIndicator(Widget):
    current_pressure: reactive[float] = reactive(-1)

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label(
                f"Reading pressure... {self.current_pressure}", id="pressure-display"
            )

    def watch_current_pressure(self, pressure: int) -> None:
        """Update the label when pressure changes"""
        print("HEYYYY")
        try:
            label = self.query_one("#pressure-display", Label)
            label.update(f"Reading pressure... {pressure}")
        except NoMatches:
            pass


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
            yield Label("sheesh")
