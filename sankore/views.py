from PySide6 import QtWidgets as widgets


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
