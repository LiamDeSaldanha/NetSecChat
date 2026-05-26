from textual.app import App, ComposeResult
from textual.widgets import Input, Button
from textual.widget import Widget


class MyInput(Input):
    
    DEFAULT_CSS = """
    MyInput {
        width: 80%;
        height: 3;
    }
    """
    def compose(self):
        return super().compose()


class ChatMessageBar(Widget):
    

    def compose(self) -> ComposeResult:
        
        yield MyInput(placeholder="Enter message...")
        yield Button("Send")


class LayoutApp(App):
    def compose(self) -> ComposeResult:
        yield ChatMessageBar()


if __name__ == "__main__":
    app = LayoutApp()
    app.run()