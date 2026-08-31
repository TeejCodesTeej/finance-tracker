from importlib.metadata import PackageNotFoundError, version

from textual.app import App, ComposeResult
from textual.widgets import Footer, Label, Header

try:
    __version__ = version("finance-tracker")
except PackageNotFoundError:
    # Running from a source checkout without an installed distribution.
    __version__ = "0.0.0-dev"

class FinanceTrackerApp(App):
    """Entry point for the `finance-tracker` console script.

    Placeholder stub for now (ticket 2 scaffold) — the real Textual `App` and its
    placeholder screen land in ticket 8.
    """
    
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("ctrl+q", "quit", "Quit")]
    
    def compose(self) -> ComposeResult:
        """Create placeholder child widgets for the app."""
        yield Header()
        yield Label(f"Finance Tracker v{__version__}")
        yield Footer()
    
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


def main():
    """Entry point for the `finance-tracker` console script."""
    app = FinanceTrackerApp()
    app.run()


if __name__ == "__main__":
    main()