from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtGui import QColor
from PySide6 import QtWidgets as widgets

ALL_BOOKS_NAME = "All Books"
APP_NAME = "Sankore"

libraries = {
    "To Read": (
        ("On The Laws", "Marcus Cicero", 544),
        ("History of the Peloponnesian War", "Thucydides", 648),
    ),
    "Already Read": (
        ("The Gallic War", "Julius Caesar", 470),
        ("The Civil War", "Julius Caesar", 368),
        ("Meditations", "Marcus Aurelius", 254),
    ),
    "Currently Reading": (
        ("On The Ideal Orator", "Marcus Cicero", 384),
        ("Peace of Mind", "Lucius Seneca", 44),
    ),
    "On Hiatus": (
        ("Metamorphoses", "Ovid", 723),
        ("Aeneid", "Virgil", 442),
    ),
}
get_all_books = lambda: sum(libraries.values(), ())
get_book_list = lambda name: (
    get_all_books() if name == ALL_BOOKS_NAME else libraries[name]
)
get_library_names = lambda: [ALL_BOOKS_NAME] + list(libraries.keys())


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
    columns = ("Title", "Author(s)", "No. of pages")

    def __init__(self):
        super().__init__()

        self.combo = widgets.QComboBox()
        self.combo.addItems(get_library_names())
        self.combo.currentTextChanged.connect(self.update_table)
        self.table = widgets.QTableWidget()
        self.table.setSizeAdjustPolicy(widgets.QAbstractScrollArea.AdjustToContents)
        self.update_table(self.combo.currentText())

        update_button = widgets.QPushButton("Update Reading Position")
        update_button.clicked.connect(self.update_progress)

        progress_widget = widgets.QWidget()
        progress_layout = widgets.QVBoxLayout()
        progress_title = widgets.QLabel("Monthly Progress")
        progress_text = widgets.QLabel("You've completed 4 books this month!")
        progress_bar = widgets.QProgressBar()
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(progress_text)
        progress_layout.addWidget(progress_bar)
        progress_widget.setLayout(progress_layout)

        layout = widgets.QGridLayout()
        layout.addWidget(self.combo, 0, 0, 1, 5)
        layout.addWidget(self.table, 1, 0, 4, 5)
        layout.addWidget(update_button, 0, 6, 1, 2)
        layout.addWidget(progress_title, 1, 6, 1, 2)
        layout.addWidget(progress_text, 2, 6, 2, 2)
        layout.addWidget(progress_bar, 3, 6, 1, 2)
        self.setLayout(layout)

    def update_progress(self):
        dialog = BookListDialog(self)
        dialog.exec()

    def update_table(self, lib_name):
        book_list = get_book_list(lib_name)
        self.table.setColumnCount(3)
        self.table.setRowCount(len(book_list))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setVerticalHeaderLabels((None,) * self.table.rowCount())
        for row_index, row in enumerate(book_list):
            for col_index, value in enumerate(row):
                self.table.setItem(
                    row_index, col_index, widgets.QTableWidgetItem(str(value))
                )

        self.table.resizeColumnsToContents()
