from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

class FinanceTrackerApp(App):
    """Entry point for the `finance-tracker` console script.

    Stub for now (ticket 2 scaffold) — the real Textual `App` and its
    placeholder screen land in ticket 8.
    """
    
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    
    def compose(self) -> ComposeResult:
        """Create placeholder child widgets for the app."""
        yield Header()
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