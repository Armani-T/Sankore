# TODO: Create a function that takes a dict and uses it to update and
# save a book that already exists.
from functools import partial
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QIcon, QPixmap, QRegularExpressionValidator
from PySide6 import QtWidgets as widgets

import models

normalise = lambda value, maximum, minimum=0: min(max(minimum, value), maximum)

_asset_folder = Path(__file__).joinpath("../../assets").resolve()
NUMBER_VALIDATOR = QRegularExpressionValidator(QRegularExpression(r"\d+"))
ASSETS: dict[str, Path] = {
    "app_icon": _asset_folder / "app-icon.png",
    "about": _asset_folder / "about.md",
    "bookmark_icon": _asset_folder / "bookmark.png",
    "edit_icon": _asset_folder / "edit.png",
    "menu_icon": _asset_folder / "menu-icon.png",
    "quote_icon": _asset_folder / "quote.png",
    "shelf_icon": _asset_folder / "shelf.png",
    "star_half": _asset_folder / "star-half.png",
    "star_filled": _asset_folder / "star-filled.png",
    "star_outline": _asset_folder / "star-outline.png",
    "trash_icon": _asset_folder / "trash.png",
}


class NewBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget) -> None:
        super().__init__(parent)
        self.save_changes = False

        self.setWindowTitle("New Book")
        self.title_edit = widgets.QLineEdit()
        self.author_edit = widgets.QLineEdit()
        self.page_edit = widgets.QLineEdit()
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        save_button = widgets.QPushButton("Add to Books")
        save_button.clicked.connect(self.accept)

        layout = widgets.QFormLayout(self)
        layout.addRow("Title:", self.title_edit)
        layout.addRow("Author:", self.author_edit)
        layout.addRow("No. of pages:", self.page_edit)
        layout.addRow(save_button)

    def accept(self) -> None:
        book = self.new_book()
        self.save_changes = bool(book.title and book.author and book.pages > 0)
        return super().done(0)

    def new_book(self) -> models.Book:
        return models.Book(
            title=self.title_edit.text().strip(),
            author=self.author_edit.text().strip(),
            pages=int(self.page_edit.text() or "1"),
            rating=1,
        )


class EditBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_changes = False
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
        self.save_changes = True
        return super().done(0)

    def updated(self) -> models.Book:
        kwargs = self.book.to_dict() | {
            "title": self.title_edit.text(),
            "author": self.author_edit.text(),
            "pages": int(self.page_edit.text()),
        }
        return models.Book(**kwargs)


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
        start = self.book.current.start
        if self.is_finished():
            new_read: models.Read = {"start": start, "end": models.get_today()}
            reads = (new_read, *self.book.reads)
            return models.Book(**self.book.to_dict(), current_run=None, reads=reads)

        new_run: models.Run = {
            "start": start or models.get_today(),
            "page": self.slider.value(),
        }
        return models.Book(**self.book.to_dict(), current_run=new_run)


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
        return super().done(0)


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
        return models.Book(**self.book.to_dict(), rating=self.current_rating)


class QuoteBook(widgets.QDialog):
    def __init__(self, parent: widgets.QWidget, book: models.Book) -> None:
        super().__init__(parent)
        self.save_changes = False
        self.book = book

        self.setWindowTitle(f'Quote "{book.title.title()}" by {book.author.title()}')
        self.quote_text = widgets.QPlainTextEdit(self)
        self.page_edit = widgets.QLineEdit(self)
        self.page_edit.setValidator(NUMBER_VALIDATOR)
        save_button = widgets.QDialogButtonBox(widgets.QDialogButtonBox.Save)
        save_button.accepted.connect(self.accept)

        layout = widgets.QFormLayout(self)
        layout.addRow("Quote:", self.quote_text)
        layout.addRow("On page:", self.page_edit)
        layout.addRow(save_button)

    def accept(self) -> None:
        self.save_changes = True
        return super().done(0)

    def quote(self) -> str:
        return self.quote_text.toPlainText().strip()
