from PySide6 import QtWidgets as widgets

APP_NAME = "Sankore"

# TODO: Populate `libraries` using the DB.
libraries = {
    "All Books": (),
    "To Read": (),
    "Already Read": (),
    "Currently Reading": (),
}


class AppWindow(widgets.QMainWindow):
    """The main window which holds all the pages in the app."""

    app = widgets.QApplication()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.to_start_page()

    def run(self):
        self.show()
        self.app.exec()

    def to_start_page(self):
        start_page = StartPage()
        self.setCentralWidget(start_page)


class StartPage(widgets.QWidget):
    def __init__(self):
        super().__init__()

        self.combo = widgets.QComboBox()
        self.combo.addItems(libraries.keys())
        self.combo.currentTextChanged.connect(self.update_table)

        self.table = widgets.QTableWidget()
        self.table.resizeColumnsToContents()
        self.update_table(self.combo.currentText())

        layout = widgets.QHBoxLayout()
        left_layout = widgets.QVBoxLayout()
        left_layout.addWidget(self.combo)
        left_layout.addWidget(self.table)
        left_layout.addStretch()
        layout.addLayout(left_layout)

        update_button = widgets.QPushButton("Update reading position")
        progress_title = widgets.QLabel("My Monthly Progress")
        progress_text = widgets.QLabel("You've completed 4 books this month!")
        progress_bar = widgets.QProgressBar()

        right_layout = widgets.QVBoxLayout()
        right_layout.addWidget(update_button)
        right_layout.addWidget(progress_title)
        right_layout.addWidget(progress_text)
        right_layout.addWidget(progress_bar)
        right_layout.addStretch()
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def update_table(self, library):
        ...
