from PySide6 import QtCore as core
from PySide6 import QtGui as gui
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
        self.model = LibraryModel()

        self.combo = widgets.QComboBox()
        self.combo.addItems(libraries.keys())
        self.combo.currentTextChanged.connect(self.update_table)

        self.table = widgets.QTableView()
        self.table.resizeRowsToContents()
        self.table.setModel(self.model)
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

    def update_table(self, lib_name):
        books = libraries.get(lib_name, "All Books")


class LibraryModel(core.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = libraries  # TODO: Populate this using the DB.

    def _index_data(self, col):
        col = col % self.columnCount(None)
        print(self._data["All Books"])
        return self._data["All Books"][col]

    def columnCount(self, _):
        return 3

    def rowCount(self, _):
        return len(self._data)

    def headerData(self, section, orientation, role):
        if role != core.Qt.DisplayRole:
            return None
        if orientation == core.Qt.Horizontal:
            return ("Title", "Author(s)", "Number of Pages")[section]
        return None

    def data(self, index, role=core.Qt.DisplayRole):
        row, col = index.row(), index.column()
        if role == core.Qt.BackgroundRole:
            return gui.QColor(core.Qt.white)
        if role == core.Qt.TextAlignmentRole:
            return gui.QColor(core.Qt.AlignRight)
        if role == core.Qt.DisplayRole:
            return self._index_data(col)
        return None
