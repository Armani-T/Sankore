from PySide6 import QtWidgets as widgets

APP_NAME = "Sankore"


class StartPage(widgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)

        layout = widgets.QHBoxLayout(self)
        self.setLayout(layout)

        left_layout = widgets.QVBoxLayout()
        left_layout.addStretch()
        layout.addLayout(left_layout)

        right_layout = widgets.QVBoxLayout()
        right_layout.addStretch()
        layout.addLayout(right_layout)


def run_ui() -> int:
    """
    Construct and run the app UI.

    Returns
    -------
    int
        The exit code for the GUI. 0 means it stopped with no errors.
    """
    app = widgets.QApplication()
    window = StartPage()
    window.show()
    exit_code = app.exec()
    return exit_code
