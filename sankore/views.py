from pathlib import Path
from typing import Optional

from PySide6.QtCore import QCoreApplication, QRegularExpression, Qt
from PySide6.QtGui import QIcon, QPixmap, QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models

ASSET_FOLDER = Path(__file__).joinpath("../../assets").resolve()
NUMBER_VALIDATOR = QRegularExpressionValidator(QRegularExpression(r"\d+"))
ASSETS: dict[str, Path] = {
    "app_icon": ASSET_FOLDER / "app-icon.png",
    "about_file": ASSET_FOLDER / "about.md",
    "menu_icon": ASSET_FOLDER / "menu-icon.png",
}


class Home(widgets.QMainWindow):
    def __init__(self, title: str, data: models.Data) -> None:
        super().__init__()
        self.data = data
        self.libraries = sorted(models.list_libraries(data, False))
        self.pages = {}

        self.tabs = widgets.QTabWidget(self)
        QCoreApplication.setApplicationName("Sankore")
        self.setWindowIcon(QIcon(QPixmap(ASSETS["app_icon"])))
        self.setCentralWidget(self.tabs)
        self.setWindowTitle(title)

        new_menu = self.menuBar().addMenu("New")
        about_menu = self.menuBar().addMenu("About")
        new_book_action = new_menu.addAction("New Book")
        new_lib_action = new_menu.addAction("New Library")
        about_action = about_menu.addAction("About")
        new_book_action.triggered.connect(self.new_book)
        new_lib_action.triggered.connect(self.new_lib)
        about_action.triggered.connect(self.show_about)

        for name in self.libraries:
            self.pages[name] = self.create_tab_page(name)
            self.tabs.addTab(self.pages[name], name)

    def create_tab_page(self, lib_name: str) -> widgets.QWidget:
        scroll_area = widgets.QScrollArea(self.tabs)
        card_view = CardView(self, self.data)
        card_view.update_view(lib_name)
        scroll_area.setWidget(card_view)
        scroll_area.setAlignment(Qt.AlignTop)
        scroll_area.setWidgetResizable(True)
        return scroll_area

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
        name = dialog.name()
        self.libraries = sorted((*self.libraries, name))
        tab_index = self.libraries.index(name)
        self.tabs.insertTab(tab_index, self.create_tab_page(name), name)
        return result

    def show_about(self) -> int:
        about_text = ASSETS["about_file"].read_text()
        dialog = widgets.QDialog(self)
        about_label = widgets.QLabel(dialog)
        about_label.setAlignment(Qt.AlignCenter)
        about_label.setTextFormat(Qt.MarkdownText)
        about_label.setText(about_text)
        return dialog.exec()


class CardView(widgets.QWidget):
    def __init__(self, parent: Home, data: models.Data) -> None:
        super().__init__(parent)
        self.library: str = models.ALL_BOOKS
        self.data = data
        self.setSizePolicy(
            widgets.QSizePolicy.Minimum,
            widgets.QSizePolicy.MinimumExpanding,
        )
        self.layout_ = widgets.QGridLayout(self)

    def populate(self) -> None:
        row, col = 0, 0
        show_progress = (
            self.library != models.ALL_BOOKS
            and self.data[self.library]["page_tracking"]
        )
        books = sorted(
            models.list_books(self.data, self.library),
            key=lambda book: book["title"],
        )
        for book in books:
            card = Card(self, book, show_progress)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def clear(self) -> None:
        while (child := self.layout_.takeAt(0)) is not None:
            card = child.widget()
            card.deleteLater()

    def update_view(self, library: Optional[str] = None) -> None:
        self.library = library or self.library
        self.clear()
        self.populate()

    def update_progress(self, book: models.Book) -> int:
        lib_name = "Currently Reading"
        dialog = UpdateProgress(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes:
            updated_book = {**book, "current_page": dialog.value()}
            models.update_book(self.data, book, updated_book, lib_name)
            pages = self.parent().pages
            pages[lib_name].update_view()
        return exit_code


class Card(widgets.QFrame):
    def __init__(
        self, parent: CardView, book: models.Book, show_progress: bool = False
    ) -> None:
        super().__init__(parent)
        self.book = book
        self.show_progress = show_progress
        self.setSizePolicy(
            widgets.QSizePolicy.MinimumExpanding,
            widgets.QSizePolicy.MinimumExpanding,
        )
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        layout = widgets.QVBoxLayout(self)
        title_layout = widgets.QHBoxLayout()
        title = widgets.QLabel(book["title"].title())
        tool_button = widgets.QToolButton(self)
        tool_button.setIcon(QIcon(QPixmap(ASSETS["menu_icon"])))
        tool_button.setPopupMode(widgets.QToolButton.InstantPopup)
        tool_button.setAutoRaise(True)
        tool_button.setMenu(self.setup_menu())
        title_layout.addWidget(title, alignment=Qt.AlignLeft)
        title_layout.addWidget(tool_button, alignment=Qt.AlignRight)
        layout.addLayout(title_layout)

        author = widgets.QLabel(book["author"].title())
        layout.addWidget(author, alignment=Qt.AlignLeft)
        pages = widgets.QLabel(f"{book['pages']} Pages")
        layout.addWidget(pages, alignment=Qt.AlignLeft)
        if self.show_progress:
            progress = widgets.QProgressBar()
            progress.setMaximum(book["pages"])
            progress.setValue(min(max(0, book["current_page"]), book["pages"]))
            layout.addWidget(progress, alignment=Qt.AlignLeft)

    def delete_(self) -> None:
        # TODO: Implement this function.
        ...

    def edit_(self) -> int:
        dialog = EditBook(self, self.book)
        result = dialog.exec()
        if not result and dialog.save_edits:
            parent: CardView = self.parent()
            new_book = dialog.updated_book()
            lib_name = models.find_library(parent.data, self.book)
            models.update_book(parent.data, self.book, new_book, lib_name)
            parent.update_view()
            return 0
        return result

    def setup_menu(self) -> widgets.QMenu:
        menu = widgets.QMenu(self)
        if self.show_progress:
            update_action = menu.addAction("Update reading progress")
            update_action.triggered.connect(self.update_)

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(self.edit_)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_)
        return menu

    def update_(self) -> None:
        parent = self.parent()
        return parent.update_progress(self.book)


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
            pages
            if self.library() == "Already Read"
            else 1
            if self.data[self.library()]["page_tracking"]
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


class NewLibrary(widgets.QDialog):
    def __init__(self, data: models.Data, parent: widgets.QWidget) -> None:
        super().__init__(parent)
        self.data = data

        self.setWindowTitle("New Library")
        self.name_edit = widgets.QLineEdit(self)
        self.description_edit = widgets.QPlainTextEdit(self)
        self.page_tracking = widgets.QCheckBox(self)
        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.save)

        layout = widgets.QFormLayout(self)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Page Tracking:", self.page_tracking)
        layout.addRow(save_button)

    def name(self) -> str:
        return self.name_edit.text().strip().title()

    def save(self) -> None:
        exit_code = 0
        new_lib: models.Library = {
            "description": self.description_edit.toPlainText().strip(),
            "books": [],
            "page_tracking": self.page_tracking.isChecked(),
        }
        if name := self.name():
            exit_code, new_data = models.create_lib(self.data, name, new_lib)
            self.data = new_data
        return super().done(exit_code)


# TODO: Add a way to change the library too.
class EditBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.book = book
        self.save_edits = False

        self.setWindowTitle(f'Editing "{book["title"]}"')
        self.title_edit = widgets.QLineEdit()
        self.title_edit.setText(book["title"])
        self.author_edit = widgets.QLineEdit()
        self.author_edit.setText(book["author"])
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.setText(str(book["pages"]))

        save_button = widgets.QPushButton("Update")
        save_button.clicked.connect(self._save)

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow(save_button)

    def _save(self) -> None:
        self.save_edits = True
        return super().done(0)

    def updated_book(self) -> models.Book:
        pages = int(self.page_edit.text())
        return {
            "title": self.title_edit.text(),
            "author": self.author_edit.text(),
            "pages": pages,
            "current_page": min(self.book["current_page"], pages),
        }


class UpdateProgress(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_changes = False

        title = widgets.QLabel(f"<h1>{book['title'].title()}</h1>")
        title.setAlignment(Qt.AlignCenter)
        left_text = widgets.QLabel("Reached page")
        left_text.setAlignment(Qt.AlignRight)
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.textChanged.connect(self.update_slider)
        right_text = widgets.QLabel(f"out of {book['pages']}.")
        right_text.setAlignment(Qt.AlignLeft)

        self.slider = widgets.QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(book["pages"])
        self.slider.setTracking(False)
        self.slider.valueChanged.connect(self.update_edit)
        self.slider.setValue(book["current_page"])

        finished_button = widgets.QPushButton("Finished the book")
        finished_button.clicked.connect(
            lambda: self.slider.setValue(self.slider.maximum())
        )
        button_box = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        button_box.accepted.connect(self.save_)
        button_box.rejected.connect(lambda: self.done(1))

        layout = widgets.QGridLayout(self)
        layout.addWidget(title, 0, 1, 1, 3)
        layout.addWidget(left_text, 1, 0, 1, 2)
        layout.addWidget(self.page_edit, 1, 2, 1, 1)
        layout.addWidget(right_text, 1, 3, 1, 2)
        layout.addWidget(self.slider, 2, 1, 1, 3)
        layout.addWidget(finished_button, 3, 2, 1, 1)
        layout.addWidget(button_box, 4, 0, 1, 5)

    def save_(self) -> None:
        self.save_changes = True
        return super().done(0)

    def update_edit(self) -> None:
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
