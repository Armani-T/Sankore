from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models

NUMBER_VALIDATOR = QRegularExpressionValidator(QRegularExpression(r"\d+"))


class HomePage(widgets.QWidget):
    columns = ("Title", "Author(s)", "No. of pages")

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data

        self.combo = widgets.QComboBox()
        self.combo.addItems(tuple(models.list_libraries(self.data)))
        self.combo.currentTextChanged.connect(self.update_table)

        self.table = widgets.QTableWidget()
        self.table.setSizeAdjustPolicy(widgets.QAbstractScrollArea.AdjustToContents)
        self.update_table(self.combo.currentText())

        new_book_button = widgets.QPushButton("New Book")
        update_button = widgets.QPushButton("Update Reading Position")
        new_book_button.clicked.connect(self.new_book)
        update_button.clicked.connect(self.update_progress)

        progress_widget = widgets.QWidget()
        progress_layout = widgets.QVBoxLayout()
        progress_title = widgets.QLabel("<h2>Monthly Progress</h2>")
        progress_title.setAlignment(Qt.AlignCenter)
        progress_text = widgets.QLabel("You've completed 4 books this month!")
        progress_text.setAlignment(Qt.AlignCenter)
        progress_bar = widgets.QProgressBar()
        progress_layout.addWidget(progress_title)
        progress_layout.addWidget(progress_text)
        progress_layout.addWidget(progress_bar)
        progress_widget.setLayout(progress_layout)

        layout = widgets.QGridLayout()
        layout.addWidget(self.combo, 0, 0, 1, 8)
        layout.addWidget(self.table, 1, 0, 8, 8)
        layout.addWidget(update_button, 0, 8, 1, 4)
        layout.addWidget(new_book_button, 1, 8, 1, 4)
        layout.addWidget(progress_widget, 6, 8, 3, 4)
        self.setLayout(layout)

    def new_book(self):
        dialog = NewBook(self.data, self)
        result = dialog.exec()
        library = dialog.library()
        all_libs = tuple(models.list_libraries(self.data))
        self.combo.setCurrentIndex(all_libs.index(library))
        self.update_table(library)
        return result

    def update_progress(self):
        dialog = UpdateProgress(self, self.data)
        return dialog.exec()

    def update_table(self, lib_name):
        book_list = models.list_books(self.data, lib_name)
        self.table.setColumnCount(len(self.columns))
        self.table.setRowCount(len(book_list))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setVerticalHeaderLabels([""] * self.table.rowCount())
        for index, book in enumerate(book_list):
            self.table.setItem(index, 0, widgets.QTableWidgetItem(book.title))
            self.table.setItem(index, 1, widgets.QTableWidgetItem(book.author))
            self.table.setItem(index, 2, widgets.QTableWidgetItem(str(book.pages)))

        self.table.resizeColumnsToContents()


class NewBook(widgets.QDialog):
    def __init__(self, data, parent):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Add a book")
        self.title_edit = widgets.QLineEdit()
        self.author_edit = widgets.QLineEdit()
        self.page_edit = widgets.QLineEdit()
        self.combo = widgets.QComboBox()
        self.combo.addItems(tuple(models.list_libraries(self.data, False)))
        self.page_edit.setValidator(NUMBER_VALIDATOR)

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
            models.insert_book(
                self.data, self.library(), models.Book(title, author, pages)
            )
        return super().done(0)

    def library(self):
        return self.combo.currentText()


class UpdateProgress(widgets.QDialog):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.layout = widgets.QStackedLayout()
        self.list_widget = self._create_list()
        self.layout.addWidget(self.list_widget)
        self.setLayout(self.layout)
        self.to_list()

    def _create_list(self):
        base = widgets.QWidget(self)
        layout = widgets.QVBoxLayout()
        base.setLayout(layout)

        layout.addWidget(widgets.QLabel("<h1>Choose a Book to Update</h1>"))
        for book in models.list_books(self.data, "Currently Reading"):
            button = widgets.QPushButton(book.title)
            button.clicked.connect(
                lambda *_, title_=book.title: self.to_updater(title_)
            )
            layout.addWidget(button)

        return base

    def _create_updater(self, book_title):
        book = models.find_book(self.data, book_title)
        base = widgets.QWidget(self)

        title = widgets.QLabel(f"<h1>{book.title.title()}</h1>")
        title.setAlignment(Qt.AlignCenter)
        left_text = widgets.QLabel("Reached page")
        self.page_edit = widgets.QLineEdit()
        right_text = widgets.QLabel(f"out of {book.pages}.")
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.textChanged.connect(self.update_slider)

        self.slider = widgets.QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(book.pages)
        self.slider.setTracking(False)
        self.slider.valueChanged.connect(self.update_editor)
        self.slider.setValue(book.current_page)

        finished_button = widgets.QPushButton("Finished the book")
        finished_button.clicked.connect(
            lambda: self.slider.setValue(self.slider.maximum())
        )
        button_box = widgets.QDialogButtonBox(
            widgets.QDialogButtonBox.Save | widgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.update_progress)
        button_box.rejected.connect(self.to_list)

        layout = widgets.QGridLayout()
        layout.addWidget(title, 0, 1, 1, 3)
        layout.addWidget(left_text, 1, 0, 1, 2)
        layout.addWidget(self.page_edit, 1, 2, 1, 1)
        layout.addWidget(right_text, 1, 3, 1, 2)
        layout.addWidget(self.slider, 2, 1, 1, 3)
        layout.addWidget(finished_button, 3, 2, 1, 1)
        layout.addWidget(button_box, 4, 0, 1, 5)
        base.setLayout(layout)
        return base

    def update_progress(self):
        return super().done(0)

    def to_updater(self, title):
        self.setWindowTitle(f'Updating "{title.title()}"')
        widget = self._create_updater(title)
        self.layout.addWidget(widget)
        self.layout.setCurrentWidget(widget)

    def to_list(self):
        self.setWindowTitle("Choose a Book to Update")
        self.layout.setCurrentWidget(self.list_widget)

    def update_editor(self):
        new_value = str(self.slider.value())
        self.page_edit.setText(new_value)

    def update_slider(self):
        new_value = int(self.page_edit.text() or "0")
        self.slider.setValue(new_value)


def run_ui(title: str, data: models.Data) -> int:
    app = widgets.QApplication()
    window = widgets.QMainWindow()
    window.setWindowTitle(title)
    window.setCentralWidget(HomePage(data, window))
    window.show()
    return app.exec()
