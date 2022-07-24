from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor
from PySide6 import QtWidgets as widgets

APP_NAME = "Sankore"

libraries = {
    "All Books": (
        ("The Gallic War", "Julius Caesar", 470),
        ("The Civil War", "Julius Caesar", 368),
        ("Meditations", "Marcus Aurelius", 254),
        ("On The Laws", "Marcus Cicero", 544),
        ("On The Ideal Orator", "Marcus Cicero", 384),
    ),
    "To Read": (("On The Laws", "Marcus Cicero", 544),),
    "Already Read": (
        ("The Gallic War", "Julius Caesar", 470),
        ("The Civil War", "Julius Caesar", 368),
        ("Meditations", "Marcus Aurelius", 254),
    ),
    "Currently Reading": (("On The Ideal Orator", "Marcus Cicero", 384),),
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
        self.update_table(self.combo.currentText())

        layout = widgets.QHBoxLayout()
        self.setLayout(layout)
        left_layout = widgets.QVBoxLayout()
        left_layout.addWidget(self.combo)
        left_layout.addWidget(self.table)
        left_layout.addStretch()
        layout.addLayout(left_layout)

        update_button = widgets.QPushButton("Update reading position")
        update_button.clicked.connect(self.update_progress)

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

    def update_progress(self):
        dialog = BookListDialog(self)
        dialog.exec()

    def update_table(self, lib_name):
        self.table.setColumnCount(3)
        self.table.setRowCount(len(libraries[lib_name]))
        self.table.setHorizontalHeaderLabels(("Title", "Author(s)", "No. of pages"))
        self.table.setVerticalHeaderLabels((None,) * self.table.rowCount())
        for row_index, row in enumerate(libraries[lib_name]):
            for col_index, value in enumerate(row):
                self.table.setItem(
                    row_index, col_index, widgets.QTableWidgetItem(str(value))
                )


AppWindow().run()
