from textual.app import App, ComposeResult
from textual.widgets import Footer, Header


class AutoCalCli(App):
    """A textual app to get user input for linear regression calculations"""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create header and footer"""
        yield Header()
        yield Footer()

    # custom functions which are to be called should be in the form: action_func_name
    def action_toggle_dark(self) -> None:
        """Toggle appearance of cli"""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
