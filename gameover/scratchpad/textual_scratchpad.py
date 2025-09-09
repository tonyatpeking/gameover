from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Static


class ButtonsApp(App[str]):
    CSS_PATH = "button.tcss"

    def compose(self) -> ComposeResult:
        yield Horizontal(
            VerticalScroll(
                Static("Fla", classes="header"),
                Button("Def", flat=True, compact=True),
                Button("Pri", variant="primary", flat=True, compact=True),
            ),
            VerticalScroll(
                Static("Dis", classes="header"),
                Button("Def", disabled=True, flat=True, compact=True),
                Button("Pri", variant="primary", disabled=True, flat=True, compact=True),

            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.exit(str(event.button))


if __name__ == "__main__":
    app = ButtonsApp()
    print(app.run())