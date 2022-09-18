from functools import partial
from operator import attrgetter
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtCore import QCoreApplication, QRegularExpression, Qt
from PySide6.QtGui import QIcon, QPixmap, QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models

normalise = lambda value, maximum, minimum=0: min(max(minimum, value), maximum)

ASSET_FOLDER = Path(__file__).joinpath("../../assets").resolve()
NUMBER_VALIDATOR = QRegularExpressionValidator(QRegularExpression(r"\d+"))
ASSETS: dict[str, Path] = {
    "app_icon": ASSET_FOLDER / "app-icon.png",
    "about": ASSET_FOLDER / "about.md",
    "bookmark_icon": ASSET_FOLDER / "bookmark.png",
    "edit_icon": ASSET_FOLDER / "edit.png",
    "menu_icon": ASSET_FOLDER / "menu-icon.png",
    "star_half": ASSET_FOLDER / "star-half.png",
    "star_filled": ASSET_FOLDER / "star-filled.png",
    "star_outline": ASSET_FOLDER / "star-outline.png",
    "trash_icon": ASSET_FOLDER / "trash.png",
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
        about_action.triggered.connect(self._show_about)

        for name in self.libraries:
            page, card_view = self._create_tab_page(name)
            self.pages[name] = card_view
            self.tabs.addTab(page, name)

    def _create_tab_page(self, lib_name: str) -> tuple[widgets.QWidget, "CardView"]:
        scroll_area = widgets.QScrollArea(self.tabs)
        card_view = CardView(self, lib_name)
        card_view.update_view()
        scroll_area.setWidget(card_view)
        scroll_area.setAlignment(Qt.AlignTop)
        scroll_area.setWidgetResizable(True)
        return scroll_area, card_view

    def _show_about(self) -> int:
        about_text = ASSETS["about"].read_text()
        dialog = widgets.QDialog(self)
        label = widgets.QLabel(about_text, dialog)
        label.setTextFormat(Qt.MarkdownText)
        label.setAlignment(Qt.AlignCenter)
        return dialog.exec()

    def new_book(self) -> int:
        dialog = NewBook(self, tuple(models.list_libraries(self.data, False)))
        exit_code = dialog.exec()
        if dialog.save_changes:
            lib_name = dialog.library()
            self.data = models.insert_book(self.data, lib_name, dialog.new_book())
            card_view = self.pages[lib_name]
            card_view.update_view(lib_name)
        return exit_code

    def new_lib(self) -> int:
        dialog = NewLibrary(self)
        exit_code = dialog.exec()
        if dialog.save_changes:
            name = dialog.name()
            exit_code, self.data = models.create_lib(self.data, name, dialog.new_lib())
            self.libraries = sorted((*self.libraries, name))
            page, card_view = self._create_tab_page(name)
            self.pages[name] = card_view
            self.tabs.addTab(page, name)
        return exit_code


class CardView(widgets.QWidget):
    def __init__(self, parent: Home, lib_name: str) -> None:
        super().__init__(parent)
        self.home = parent
        self.lib_name = lib_name
        self.setSizePolicy(
            widgets.QSizePolicy.Minimum,
            widgets.QSizePolicy.Fixed,
        )
        self.layout_ = widgets.QGridLayout(self)
        self.layout_.setAlignment(Qt.AlignTop)

    @property
    def data(self):
        return self.home.data

    @data.setter
    def data(self, new_data):
        self.home.data = new_data

    def populate(self) -> None:
        row, col = 0, 0
        show_rating = self.lib_name == "Already Read"
        show_progress = (
            self.lib_name != models.ALL_BOOKS and self.data[self.lib_name].page_tracking
        )
        books = sorted(
            models.list_books(self.data, self.lib_name), key=attrgetter("title")
        )
        for book in books:
            card = Card(self, book, show_progress, show_rating)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def clear(self) -> None:
        while (child := self.layout_.takeAt(0)) is not None:
            card = child.widget()
            card.deleteLater()

    def edit_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.data, book)
        dialog = EditBook(self, book)
        exit_code = dialog.exec()
        if dialog.save_edits and lib_name is not None:
            new_book = dialog.updated()
            self.data = models.update_book(self.data, book, new_book, lib_name)
            self.update_view(lib_name)
        return exit_code

    def delete_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.data, book)
        dialog = AreYouSure(self, book.title)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            self.data = models.remove_book(self.data, book, lib_name)
            self.update_view(lib_name)
        return exit_code

    def rate_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.data, book)
        dialog = RateBook(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            self.data = models.update_book(self.data, book, dialog.updated(), lib_name)
            self.update_view(lib_name)
        return exit_code

    def update_view(self, lib_name: Optional[str] = None) -> None:
        self.lib_name = lib_name or self.lib_name
        self.clear()
        self.populate()

    def update_progress(self, book: models.Book) -> int:
        lib_name = models.find_library(self.data, book)
        dialog = UpdateProgress(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            new_lib = "Already Read" if dialog.is_finished() else lib_name
            self.data = models.update_book(
                self.data, book, dialog.updated(), lib_name, new_lib
            )
            self.update_view(lib_name)
            self.update_view(new_lib)
        return exit_code


class Card(widgets.QFrame):
    def __init__(
        self,
        parent: CardView,
        book: models.Book,
        show_progress: bool = False,
        show_rating: bool = False,
    ) -> None:
        super().__init__(parent)
        self.book = book
        self.show_progress = show_progress
        self.show_rating = show_rating
        self.setSizePolicy(
            widgets.QSizePolicy.MinimumExpanding,
            widgets.QSizePolicy.MinimumExpanding,
        )
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        layout = widgets.QVBoxLayout(self)
        title_layout = widgets.QHBoxLayout()
        title = widgets.QLabel(book.title.title())
        tool_button = widgets.QToolButton(self)
        tool_button.setIcon(QIcon(QPixmap(ASSETS["menu_icon"])))
        tool_button.setPopupMode(widgets.QToolButton.InstantPopup)
        tool_button.setAutoRaise(True)
        tool_button.setMenu(self._setup_menu())
        title_layout.addWidget(title, alignment=Qt.AlignLeft)
        title_layout.addWidget(tool_button, alignment=Qt.AlignRight)
        layout.addLayout(title_layout)

        author = widgets.QLabel(book.author.title())
        layout.addWidget(author, alignment=Qt.AlignLeft)
        pages = widgets.QLabel(f"{book.pages} Pages")
        layout.addWidget(pages, alignment=Qt.AlignLeft)

        if self.show_rating:
            empty_star = QPixmap(ASSETS["star_outline"])
            filled_star = QPixmap(ASSETS["star_filled"])
            rating_bar = widgets.QWidget(self)
            bar_layout = widgets.QHBoxLayout(rating_bar)
            stars = normalise(book.rating, 5, 1)
            for index in range(1, 6):
                label = widgets.QLabel(self)
                label.setPixmap(empty_star if index > stars else filled_star)
                bar_layout.addWidget(label)
            layout.addWidget(rating_bar)
        if self.show_progress:
            bar = widgets.QProgressBar(self)
            bar.setMaximum(book.pages)
            bar.setValue(normalise(book.current_page, book.pages))
            layout.addWidget(bar)

    def _setup_menu(self) -> widgets.QMenu:
        menu = widgets.QMenu(self)
        if self.show_rating:
            rating_icon = QIcon(QPixmap(ASSETS["star_half"]))
            rating_action = menu.addAction(rating_icon, "Rate")
            rating_action.triggered.connect(self.rate_book)
        if self.show_progress:
            update_icon = QIcon(QPixmap(ASSETS["bookmark_icon"]))
            update_action = menu.addAction(update_icon, "Update reading progress")
            update_action.triggered.connect(self.update_progress)
        if self.show_rating or self.show_progress:
            menu.addSeparator()

        edit_icon = QIcon(QPixmap(ASSETS["edit_icon"]))
        edit_action = menu.addAction(edit_icon, "Edit")
        edit_action.triggered.connect(self.edit_book)
        delete_icon = QIcon(QPixmap(ASSETS["trash_icon"]))
        delete_action = menu.addAction(delete_icon, "Delete")
        delete_action.triggered.connect(self.delete_book)
        return menu

    def delete_book(self) -> int:
        parent: CardView = self.parent()
        return parent.delete_book(self.book)

    def edit_book(self) -> int:
        parent: CardView = self.parent()
        return parent.edit_book(self.book)

    def rate_book(self) -> int:
        parent: CardView = self.parent()
        return parent.rate_book(self.book)

    def update_progress(self) -> int:
        parent: CardView = self.parent()
        return parent.update_progress(self.book)


class NewBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, libraries: Sequence[str]) -> None:
        super().__init__(parent)
        self.save_changes = False

        self.setWindowTitle("New Book")
        self.title_edit = widgets.QLineEdit()
        self.author_edit = widgets.QLineEdit()
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.combo = widgets.QComboBox()
        self.combo.addItems(libraries)
        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.accept)

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow("Library:", self.combo)
        layout.addRow(save_button)

    def accept(self) -> None:
        book = self.new_book()
        self.save_changes = book.title and book.author and book.pages > 0
        return super().done(0)

    def library(self) -> str:
        return self.combo.currentText()

    def new_book(self) -> models.Book:
        pages = int(self.page_edit.text() or "1")
        current_page = pages if self.library() == "Already Read" else 0
        return models.Book(
            title=self.title_edit.text().strip(),
            author=self.author_edit.text().strip(),
            pages=pages,
            current_page=current_page,
            rating=1,
        )


class NewLibrary(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget) -> None:
        super().__init__(parent)
        self.save_changes = False

        self.setWindowTitle("New Library")
        self.name_edit = widgets.QLineEdit(self)
        self.description_edit = widgets.QPlainTextEdit(self)
        self.page_tracking = widgets.QCheckBox(self)
        self.can_rate = widgets.QCheckBox(self)
        save_button = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        save_button.accepted.connect(self.accept)

        layout = widgets.QFormLayout(self)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Page Tracking:", self.page_tracking)
        layout.addRow("Rate Books:", self.can_rate)
        layout.addRow(save_button)

    def accept(self) -> None:
        self.save_changes = bool(self.name())
        return super().done(0)

    def name(self) -> str:
        return self.name_edit.text().strip().title()

    def new_lib(self) -> models.Library:
        return models.Library(
            books=(),
            description=self.description_edit.toPlainText().strip(),
            page_tracking=self.page_tracking.isChecked(),
            can_rate=self.can_rate.isChecked(),
        )


# TODO: Add a way to change the library too.
class EditBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_edits = False
        self.book = book

        self.setWindowTitle(f'Editing "{book.title}"')
        self.title_edit = widgets.QLineEdit()
        self.title_edit.setText(book.title)
        self.author_edit = widgets.QLineEdit()
        self.author_edit.setText(book.author)
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.setText(str(book.pages))

        save_button = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        save_button.accepted.connect(self.accept)

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow(save_button)

    def accept(self) -> None:
        self.save_edits = True
        return super().done(0)

    def updated(self) -> models.Book:
        pages = int(self.page_edit.text())
        return models.Book(
            title=self.title_edit.text(),
            author=self.author_edit.text(),
            pages=pages,
            current_page=min(self.book.current_page, pages),
            rating=self.book.rating,
        )


class UpdateProgress(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_changes = False
        self.book = book

        title = widgets.QLabel(f"<h1>{book.title.title()}</h1>")
        title.setAlignment(Qt.AlignCenter)
        left_text = widgets.QLabel("Reached page")
        left_text.setAlignment(Qt.AlignRight)
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        self.page_edit.textChanged.connect(self._update_slider)
        right_text = widgets.QLabel(f"out of {book.pages}.")
        right_text.setAlignment(Qt.AlignLeft)

        self.slider = widgets.QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(book.pages)
        self.slider.setTracking(False)
        self.slider.valueChanged.connect(self._update_edit)
        self.slider.setValue(book.current_page)

        finished_button = widgets.QPushButton("Finished the book")
        finished_button.clicked.connect(
            lambda: self.slider.setValue(self.slider.maximum())
        )
        button_box = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        button_box.accepted.connect(self.save_)

        layout = widgets.QGridLayout(self)
        layout.addWidget(title, 0, 1, 1, 3)
        layout.addWidget(left_text, 1, 0, 1, 2)
        layout.addWidget(self.page_edit, 1, 2, 1, 1)
        layout.addWidget(right_text, 1, 3, 1, 2)
        layout.addWidget(self.slider, 2, 1, 1, 3)
        layout.addWidget(finished_button, 3, 2, 1, 1)
        layout.addWidget(button_box, 4, 0, 1, 5)

    def _update_edit(self) -> None:
        new_value = str(self.slider.value())
        self.page_edit.setText(new_value)

    def _update_slider(self) -> None:
        new_value = int(self.page_edit.text() or "0")
        self.slider.setValue(new_value)

    def is_finished(self) -> bool:
        return self.book.pages == self.slider.value()

    def save_(self) -> None:
        self.save_changes = True
        return super().done(0)

    def updated(self) -> models.Book:
        return models.Book(
            title=self.book.title,
            author=self.book.author,
            pages=self.book.pages,
            current_page=self.slider.value(),
            rating=self.book.rating,
        )


class AreYouSure(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book_title: str) -> None:
        super().__init__(parent)
        self.save_changes = False

        label = widgets.QLabel(
            f"Are you sure you want to delete <em>{book_title.title()}</em>?"
        )
        label.setAlignment(Qt.AlignCenter)
        button_box = widgets.QDialogButtonBox(
            widgets.QDialogButtonBox.Yes | widgets.QDialogButtonBox.No
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = widgets.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(button_box)

    def accept(self) -> None:
        self.save_changes = True
        return super().done(0)

    def reject(self) -> None:
        self.save_changes = False
        return super().done(1)


class RateBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_changes = False
        self.book = book
        self.current_rating = book.rating

        layout = widgets.QVBoxLayout(self)
        layout.addWidget(
            widgets.QLabel(
                f"How would you rate <em>{book.title.title()}</em> by "
                f"<em>{book.author.title()}</em>?"
            )
        )

        self.stars = self._create_stars()
        self._update_stars()
        star_layout = widgets.QHBoxLayout()
        layout.addLayout(star_layout)
        for star in self.stars:
            star_layout.addWidget(star)

        save_button = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        save_button.accepted.connect(self.accept)
        layout.addWidget(save_button)

    def accept(self):
        self.save_changes = True
        return super().done(0)

    def _create_stars(self):
        stars = []
        for index in range(1, 6):
            star = widgets.QToolButton(self)
            star.clicked.connect(partial(self._update_stars, index))
            star.setAutoRaise(True)
            stars.append(star)
        return stars

    def _update_stars(self, rating: Optional[int] = None):
        self.current_rating = normalise(
            (self.current_rating if rating is None else rating), 5, 1
        )
        empty_star = QIcon(QPixmap(ASSETS["star_outline"]))
        filled_star = QIcon(QPixmap(ASSETS["star_filled"]))
        for index, star in enumerate(self.stars, start=1):
            star.setIcon(empty_star if index > self.current_rating else filled_star)

    def updated(self):
        return models.Book(
            title=self.book.title,
            author=self.book.author,
            pages=self.book.pages,
            current_page=self.book.current_page,
            rating=self.current_rating,
        )


def run_ui(title: str, data: models.Data) -> tuple[models.Data, int]:
    app = widgets.QApplication()
    window = Home(title, data)
    window.show()
    exit_status = app.exec()
    return window.data, exit_status
