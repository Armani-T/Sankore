from typing import Optional

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models

NUMBER_VALIDATOR = QRegularExpressionValidator(QRegularExpression(r"\d+"))


class Home(widgets.QMainWindow):
    def __init__(self, title: str, data: models.Data):
        super().__init__()
        self.setWindowTitle(title)
        self.data = data
        self.base = widgets.QWidget(self)
        self.setCentralWidget(self.base)

        self.combo = widgets.QComboBox(self.base)
        self.combo.addItems(tuple(models.list_libraries(self.data)))
        self.combo.currentTextChanged.connect(self.update_cards)

        scroll_area = widgets.QScrollArea(self.base)
        self.card_view = CardView(scroll_area, self.data)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.card_view)
        self.update_cards()

        new_book_button = widgets.QPushButton("New Book")
        new_lib_button = widgets.QPushButton("New Library")
        update_button = widgets.QPushButton("Update Reading Position")
        new_book_button.clicked.connect(self.new_book)
        new_lib_button.clicked.connect(self.new_lib)
        update_button.clicked.connect(self.update_progress)

        layout = widgets.QGridLayout(self.base)
        layout.addWidget(self.combo, 0, 0, 1, 10)
        layout.addWidget(scroll_area, 1, 0, 22, 10)
        layout.addWidget(update_button, 23, 0, 1, 10)
        layout.addWidget(new_lib_button, 24, 0, 1, 5)
        layout.addWidget(new_book_button, 24, 5, 1, 5)

    def new_book(self) -> int:
        dialog = NewBook(self.data, self)
        result = dialog.exec()
        self.data = dialog.data
        all_libs = tuple(models.list_libraries(self.data))
        self.combo.setCurrentIndex(all_libs.index(dialog.library()))
        self.update_cards()
        return result

    def new_lib(self) -> int:
        dialog = NewLibrary(self.data, self)
        result = dialog.exec()
        self.data = dialog.data
        self.combo.addItem(dialog.name())
        return result

    def update_cards(self) -> None:
        self.card_view.update_view(self.combo.currentText())

    def update_progress(self) -> int:
        lib_name = "Currently Reading"
        dialog = UpdateProgress(self, models.list_books(self.data, lib_name))
        result = dialog.exec()
        if result == 0 and dialog.selected_book is not None:
            models.update_book(
                self.data,
                dialog.selected_book,
                {**dialog.selected_book, "current_page": dialog.value()},
                lib_name,
            )
        self.update_cards()
        return result


class CardView(widgets.QWidget):
    def __init__(self, parent: widgets.QWidget, data: models.Data) -> None:
        super().__init__(parent)
        self.current_library: str = models.ALL_BOOKS
        self.data = data
        self.setSizePolicy(
            widgets.QSizePolicy.Minimum,
            widgets.QSizePolicy.MinimumExpanding,
        )
        self.layout_ = widgets.QGridLayout(self)

    def populate(self, library: str) -> None:
        self.current_library = library
        row, col = 0, 0
        show_progress = (
            self.current_library != models.ALL_BOOKS
            and self.data[self.current_library]["page_tracking"]
        )
        for item in models.list_books(self.data, self.current_library):
            card = Card(self, item, show_progress)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def clear(self) -> None:
        while (child := self.layout_.takeAt(0)) is not None:
            card = child.widget()
            card.deleteLater()

    def update_view(self, library: Optional[str] = None) -> None:
        self.current_library = library or self.current_library
        self.clear()
        self.populate(self.current_library)


class Card(widgets.QFrame):
    def __init__(
        self, parent: CardView, book: models.Book, show_progress: bool = False
    ) -> None:
        super().__init__(parent)
        self.book = book
        self.setSizePolicy(
            widgets.QSizePolicy.MinimumExpanding,
            widgets.QSizePolicy.MinimumExpanding,
        )
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        layout = widgets.QVBoxLayout(self)
        title_layout = widgets.QHBoxLayout()
        title = widgets.QLabel(book["title"].title())
        tool_button = widgets.QToolButton()
        tool_button.clicked.connect(self.edit)
        title_layout.addWidget(title, alignment=Qt.AlignLeft)
        title_layout.addWidget(tool_button, alignment=Qt.AlignRight)
        layout.addLayout(title_layout)

        author = widgets.QLabel(book["author"].title())
        layout.addWidget(author, alignment=Qt.AlignLeft)
        pages = widgets.QLabel(f"{book['pages']} Pages")
        layout.addWidget(pages, alignment=Qt.AlignLeft)
        if show_progress:
            progress = widgets.QProgressBar()
            progress.setMaximum(book["pages"])
            progress.setValue(min(max(0, book["current_page"]), book["pages"]))
            layout.addWidget(progress, alignment=Qt.AlignLeft)

    def edit(self) -> int:
        dialog = EditBook(self, self.book)
        result = dialog.exec()
        if result:
            return result

        parent: CardView = self.parent()
        new_book = dialog.updated_book()
        lib_name = models.find_library(parent.data, self.book)
        models.update_book(parent.data, self.book, new_book, lib_name)
        parent.update_view()
        return 0


class NewBook(widgets.QDialog):
    def __init__(self, data: models.Data, parent: widgets.QWidget) -> None:
        super().__init__(parent)
        self.data = data

        self.setWindowTitle("New Book")
        self.title_edit = widgets.QLineEdit()
        self.author_edit = widgets.QLineEdit()
        self.page_edit = widgets.QLineEdit()
        self.combo = widgets.QComboBox()
        self.combo.addItems(tuple(models.list_libraries(self.data, False)))
        self.page_edit.setValidator(NUMBER_VALIDATOR)

        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.save)

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow("Library:", self.combo)
        layout.addRow(save_button)

    def save(self) -> None:
        pages = int(self.page_edit.text() or "1")
        current_page = (
            pages if self.library() == "Already Read"
            else 1 if self.data[self.library()]["page_tracking"]
            else 0
        )
        new_book: models.Book = {
            "title": self.title_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "pages": pages,
            "current_page": current_page,
        }
        if new_book["title"] and new_book["author"] and new_book["pages"] != 0:
            models.insert_book(self.data, self.library(), new_book)
            return super().done(0)
        return super().done(1)

    def library(self) -> str:
        return self.combo.currentText()


# TODO: Add a way to change the library too.
class EditBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.book = book

        self.setWindowTitle(f'Editing "{book["title"]}"')
        self.title_edit = widgets.QLineEdit()
        self.title_edit.setText(book["title"])
        self.author_edit = widgets.QLineEdit()
        self.author_edit.setText(book["author"])
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.setText(str(book["pages"]))

        save_button = widgets.QPushButton("Update")
        save_button.clicked.connect(lambda: self.done(0))

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow(save_button)

    def updated_book(self) -> models.Book:
        return {
            "title": self.title_edit.text() or self.book["title"],
            "author": self.author_edit.text() or self.book["author"],
            "pages": int(self.page_edit.text()) or self.book["pages"],
            "current_page": self.book["current_page"],
        }


class NewLibrary(widgets.QDialog):
    def __init__(self, data: models.Data, parent: widgets.QWidget) -> None:
        super().__init__(parent)
        self.data = data

        self.setWindowTitle("New Library")
        self.name_edit = widgets.QLineEdit()
        self.description_edit = widgets.QPlainTextEdit()
        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.save)

        layout = widgets.QFormLayout(self)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow(save_button)

    def name(self) -> str:
        return self.name_edit.text().strip().title()

    def save(self) -> None:
        new_lib: models.Library = {
            "description": self.description_edit.toPlainText().strip(),
            "books": [],
        }
        exit_code, new_data = models.create_lib(self.data, self.name(), new_lib)
        self.data = new_data
        return super().done(exit_code)


class UpdateProgress(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, books: list[models.Book]) -> None:
        super().__init__(parent)
        self.books: list[models.Book] = books
        self.selected_book: Optional[models.Book] = None
        self.layout_ = widgets.QStackedLayout(self)
        self.list_widget = self._create_list()
        self.layout_.addWidget(self.list_widget)
        self.to_list()

    def _create_list(self) -> widgets.QWidget:
        base = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(base)
        layout.addWidget(widgets.QLabel("<h1>Choose a Book to Update</h1>"))
        for book in self.books:
            button = widgets.QPushButton(book["title"])
            button.clicked.connect(lambda *_, book_=book: self.to_updater(book_))
            layout.addWidget(button)
        return base

    def _create_updater(self) -> widgets.QWidget:
        if self.selected_book is None:
            raise TypeError

        base = widgets.QWidget(self)
        title = widgets.QLabel(f"<h1>{self.selected_book['title'].title()}</h1>")
        title.setAlignment(Qt.AlignCenter)
        left_text = widgets.QLabel("Reached page")
        self.page_edit = widgets.QLineEdit()
        right_text = widgets.QLabel(f"out of {self.selected_book['pages']}.")
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.textChanged.connect(self.update_slider)

        self.slider = widgets.QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.selected_book["pages"])
        self.slider.setTracking(False)
        self.slider.valueChanged.connect(self.update_editor)
        self.slider.setValue(self.selected_book["current_page"])

        finished_button = widgets.QPushButton("Finished the book")
        finished_button.clicked.connect(
            lambda: self.slider.setValue(self.slider.maximum())
        )
        button_box = widgets.QDialogButtonBox(
            widgets.QDialogButtonBox.Save | widgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(lambda: self.done(0))
        button_box.rejected.connect(self.to_list)

        layout = widgets.QGridLayout(base)
        layout.addWidget(title, 0, 1, 1, 3)
        layout.addWidget(left_text, 1, 0, 1, 2)
        layout.addWidget(self.page_edit, 1, 2, 1, 1)
        layout.addWidget(right_text, 1, 3, 1, 2)
        layout.addWidget(self.slider, 2, 1, 1, 3)
        layout.addWidget(finished_button, 3, 2, 1, 1)
        layout.addWidget(button_box, 4, 0, 1, 5)
        return base

    def to_list(self) -> None:
        self.setWindowTitle("Choose a Book to Update")
        self.layout_.setCurrentWidget(self.list_widget)

    def to_updater(self, book: models.Book) -> None:
        try:
            self.selected_book = book
            widget = self._create_updater()
        except TypeError:
            return self.to_list()
        else:
            self.setWindowTitle(f'Updating "{book["title"].title()}"')
            self.layout_.addWidget(widget)
            self.layout_.setCurrentWidget(widget)
            return None

    def update_editor(self) -> None:
        new_value = str(self.slider.value())
        self.page_edit.setText(new_value)

    def update_slider(self) -> None:
        new_value = int(self.page_edit.text() or "0")
        self.slider.setValue(new_value)

    def value(self) -> int:
        return self.slider.value()


def run_ui(title: str, data: models.Data) -> tuple[models.Data, int]:
    app = widgets.QApplication()
    window = Home(title, data)
    window.show()
    exit_status = app.exec()
    return window.data, exit_status
