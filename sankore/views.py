from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models


class Window(widgets.QMainWindow):
    """The main window which holds all the pages in the app."""

    app = widgets.QApplication()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sankore")
        self.to_start_page()

    def run(self):
        self.show()
        return self.app.exec()

    def to_start_page(self):
        start_page = HomePage()
        self.setCentralWidget(start_page)


class HomePage(widgets.QWidget):
    columns = ("Title", "Author(s)", "No. of pages")

    def __init__(self):
        super().__init__()

        self.combo = widgets.QComboBox()
        self.combo.addItems(models.get_library_names())
        self.combo.currentTextChanged.connect(self.update_table)

        self.table = widgets.QTableWidget()
        self.table.setSizeAdjustPolicy(widgets.QAbstractScrollArea.AdjustToContents)
        self.update_table(self.combo.currentText())

        new_book_button = widgets.QPushButton("New Book")
        edit_book_button = widgets.QPushButton("Edit Book")
        update_button = widgets.QPushButton("Update Reading Position")
        new_book_button.clicked.connect(self.new_book)
        edit_book_button.clicked.connect(self.edit_book)
        update_button.clicked.connect(self.update_progress)

        progress_widget = widgets.QWidget()
        progress_layout = widgets.QVBoxLayout()
        progress_title = widgets.QLabel("<h2>Monthly Progress</h2>")
        progress_text = widgets.QLabel("You've completed 4 books this month!")
        progress_bar = widgets.QProgressBar()
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(progress_text)
        progress_layout.addWidget(progress_bar)
        progress_widget.setLayout(progress_layout)

        layout = widgets.QGridLayout()
        layout.addWidget(self.combo, 0, 0, 1, 8)
        layout.addWidget(self.table, 1, 0, 8, 8)
        layout.addWidget(new_book_button, 9, 0, 1, 4)
        layout.addWidget(edit_book_button, 9, 4, 1, 4)
        layout.addWidget(update_button, 0, 8, 1, 4)
        layout.addWidget(progress_widget, 1, 8, 3, 4)
        self.setLayout(layout)

    def new_book(self):
        dialog = NewBookDialog(self)
        result = dialog.exec()
        book_list = models.get_book_list(models.dialog.library())
        print(*book_list, sep="\n")
        return result

    def edit_book(self):
        print("Edit an existing book")

    def update_progress(self):
        dialog = BookListDialog(self)
        return dialog.exec()

    def update_table(self, lib_name):
        book_list = models.get_book_list(lib_name)
        self.table.setColumnCount(3)
        self.table.setRowCount(len(book_list))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setVerticalHeaderLabels((None,) * self.table.rowCount())
        for index, book in enumerate(book_list):
            self.table.setItem(index, 0, widgets.QTableWidgetItem(book.title))
            self.table.setItem(index, 1, widgets.QTableWidgetItem(book.author))
            self.table.setItem(index, 2, widgets.QTableWidgetItem(str(book.pages)))

        self.table.resizeColumnsToContents()


class NewBookDialog(widgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add a book")
        self.title_edit = widgets.QLineEdit()
        self.author_edit = widgets.QLineEdit()
        self.page_edit = widgets.QLineEdit()
        self.combo = widgets.QComboBox()
        self.combo.addItems(models.get_library_names())
        self.page_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"\d+"), self)
        )

        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.done)

        layout = widgets.QFormLayout()
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author(s):", self.author_edit)
        layout.addRow("Number of pages:", self.page_edit)
        layout.addRow("Library:", self.combo)
        layout.addRow(save_button)
        self.setLayout(layout)

    def done(self, *args):
        pages = int(self.page_edit.text() or "0")
        title, author = self.title_edit.text(), self.author_edit.text()
        if title and author:
            models.create_book(self.library(), title, author, pages)
        return super().done(0)

    def library(self):
        return self.combo.currentText()


class BookListDialog(widgets.QDialog):
    title = "Choose a Book to Update"

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(self.title)
        layout = widgets.QVBoxLayout()
        layout.addWidget(widgets.QLabel(f"<h2>{self.title}</h2>"))
        self.setLayout(layout)

        for book in models.get_book_list("Currently Reading"):
            button = widgets.QPushButton(book.title)
            button.clicked.connect(
                lambda *_, title_=book.title: self.update_book(title_)
            )
            layout.addWidget(button)

    def update_book(self, book_title):
        dialog = BookUpdateDialog(book_title, self)
        return dialog.exec()


class BookUpdateDialog(widgets.QDialog):
    def __init__(self, book_title, parent):
        super().__init__(parent)
        book_title = book_title.title()

        self.button_box = widgets.QDialogButtonBox(
            widgets.QDialogButtonBox.Save | widgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = widgets.QGridLayout()
        title = widgets.QLabel(f"<h1>{book_title}</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 1)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.setWindowTitle(f'Updating "{book_title}"')

    def accept(self):
        self.done(True)

    def reject(self):
        self.done(False)
