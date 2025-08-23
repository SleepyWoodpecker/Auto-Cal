from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Label
from textual.containers import HorizontalGroup, VerticalGroup, Container
from textual.validation import Number
from textual.binding import Binding


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


class CurrentCalibrationDisplay(VerticalGroup):
    """Display the current set of readings + the command prompt"""

    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-container"):
            yield CurrentCalibrationProgressIndicator()
            yield CurrentCalibrationUserInputWidget()


class CurrentCalibrationProgressIndicator(VerticalGroup):
    def compose(self) -> ComposeResult:
        with Container(id="current-calibration-progress-indicator"):
            yield Label("Reading pressure...")


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
        # ensure that the input is a valid number
        if event.validation_result:
            if event.validation_result.is_valid:
                self.set_error_label("")
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
