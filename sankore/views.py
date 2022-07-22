from PySide6 import QtWidgets as widgets

APP_NAME = "Sankore"


class StartPage(widgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.central_widget = widgets.QWidget()

        layout = widgets.QHBoxLayout()
        library_combo = widgets.QComboBox()
        library_combo.addItem("Currently Reading")
        library_table = widgets.QTableView()
        library_table.resizeColumnsToContents()
        update_button = widgets.QPushButton("Update reading position")

        left_layout = widgets.QVBoxLayout()
        left_layout.addWidget(library_combo)
        left_layout.addWidget(library_table)
        left_layout.addStretch()
        layout.addLayout(left_layout)

        right_layout = widgets.QVBoxLayout()
        right_layout.addWidget(update_button)
        right_layout.addWidget(widgets.QLabel("My Monthly Progress"))
        right_layout.addStretch()
        layout.addLayout(right_layout)

        self.setWindowTitle(APP_NAME)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(layout)


def run_ui():
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
    app.exec()
