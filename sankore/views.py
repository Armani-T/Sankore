from operator import attrgetter
from typing import Optional

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6 import QtWidgets as widgets

import dialogs
import models

CARD_SIZE_POLICY = widgets.QSizePolicy(
    widgets.QSizePolicy.Minimum, widgets.QSizePolicy.Fixed
)


class Home(widgets.QMainWindow):
    def __init__(self, title: str, data: models.Data) -> None:
        super().__init__()
        self.data = data
        self.libraries = sorted(models.list_libraries(data, False))
        self.pages = {}

        QCoreApplication.setApplicationName("Sankore")
        self.setWindowIcon(QIcon(QPixmap(dialogs.ASSETS["app_icon"])))
        self.setWindowTitle(title)

        new_menu = self.menuBar().addMenu("New")
        about_menu = self.menuBar().addMenu("About")
        new_book_action = new_menu.addAction("New Book")
        new_lib_action = new_menu.addAction("New Library")
        about_action = about_menu.addAction("About")
        new_book_action.triggered.connect(self._new_book)
        new_lib_action.triggered.connect(self._new_lib)
        about_action.triggered.connect(self._show_about)

        self.sidebar = SideBar(self)
        self.tabs = widgets.QTabWidget(self)
        for name in self.libraries:
            page, card_view = self._create_tab_page(name)
            self.pages[name] = card_view
            self.tabs.addTab(page, name)

        centre = widgets.QWidget(self)
        self.setCentralWidget(centre)
        centre_layout = widgets.QGridLayout(centre)
        centre_layout.addWidget(self.tabs, 0, 0, 1, 15)
        centre_layout.addWidget(self.sidebar, 0, 16, 1, 5)

    def _create_tab_page(self, lib_name: str) -> tuple[widgets.QWidget, "CardView"]:
        scroll_area = widgets.QScrollArea(self.tabs)
        card_view = CardView(self, lib_name)
        card_view.update_view()
        scroll_area.setWidget(card_view)
        scroll_area.setAlignment(Qt.AlignTop)
        scroll_area.setWidgetResizable(True)
        return scroll_area, card_view

    def _new_book(self) -> int:
        dialog = dialogs.NewBook(self, self.libraries)
        exit_code = dialog.exec()
        if dialog.save_changes:
            lib_name = dialog.library()
            self.data = models.insert_book(self.data, lib_name, dialog.new_book())
            card_view = self.pages[lib_name]
            card_view.update_view(lib_name)
        return exit_code

    def _new_lib(self) -> int:
        dialog = dialogs.NewLibrary(self)
        exit_code = dialog.exec()
        if dialog.save_changes:
            name = dialog.name()
            exit_code, self.data = models.create_lib(self.data, name, dialog.new_lib())
            self.libraries = sorted((*self.libraries, name))
            page, card_view = self._create_tab_page(name)
            self.pages[name] = card_view
            self.tabs.addTab(page, name)
        return exit_code

    def _show_about(self) -> int:
        about_text = (
            dialogs.ASSETS["about"].read_text()
            if dialogs.ASSETS["about"].exists()
            else "About text not found!"
        )
        dialog = widgets.QDialog(self)
        layout = widgets.QHBoxLayout(dialog)
        label = widgets.QLabel(about_text)
        label.setTextFormat(Qt.MarkdownText)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return dialog.exec()

    def go_to(self, lib_name: str) -> None:
        card_view = self.pages[lib_name]
        card_view.update_view(lib_name)
        index = self.libraries.index(lib_name)
        self.tabs.setCurrentIndex(index)

    def update_sidebar(self) -> None:
        self.sidebar.update_()


class CardView(widgets.QWidget):
    def __init__(self, parent: Home, lib_name: str) -> None:
        super().__init__(parent)
        self.home: Home = parent
        self.lib_name: str = lib_name
        self.setSizePolicy(
            widgets.QSizePolicy.Minimum,
            widgets.QSizePolicy.Fixed,
        )
        self.layout_ = widgets.QGridLayout(self)
        self.layout_.setAlignment(Qt.AlignTop)

    def _populate(self) -> None:
        row, col = 0, 0
        show_rating = self.lib_name == "Already Read"
        show_progress = (
            self.lib_name != models.ALL_BOOKS
            and self.home.data[self.lib_name].page_tracking
        )
        books = sorted(
            models.list_books(self.home.data, self.lib_name), key=attrgetter("title")
        )
        for book in books:
            card = Card(self, book, show_progress, show_rating)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def update_view(self, lib_name: Optional[str] = None) -> None:
        self.lib_name = lib_name or self.lib_name
        _clear_layout(self.layout_)
        self._populate()

    def change_library(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.ChangeLibrary(self, book.title, self.home.libraries, lib_name)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name != dialog.library():
            self.home.data = models.update_book(
                self.home.data, book, book, lib_name, dialog.library()
            )
            self.update_view(lib_name)
            self.home.go_to(dialog.library())
        return exit_code

    def delete_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.AreYouSure(self, book.title)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            self.home.data = models.remove_book(self.home.data, book, lib_name)
            self.update_view(lib_name)
        return exit_code

    def edit_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.EditBook(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            new_book = dialog.updated()
            self.home.data = models.update_book(
                self.home.data, book, new_book, lib_name
            )
            self.update_view(lib_name)
        return exit_code

    def quote_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.QuoteBook(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            new_book = models.Book(
                title=book.title,
                author=book.author,
                pages=book.pages,
                current_page=book.current_page,
                rating=book.rating,
                quotes=(*book.quotes, dialog.quote()),
            )
            self.home.data = models.update_book(
                self.home.data, book, new_book, lib_name
            )
            self.update_view(lib_name)
            self.home.update_sidebar()
        return exit_code

    def rate_book(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.RateBook(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            self.home.data = models.update_book(
                self.home.data, book, dialog.updated(), lib_name
            )
            self.update_view(lib_name)
        return exit_code

    def update_progress(self, book: models.Book) -> int:
        lib_name = models.find_library(self.home.data, book)
        dialog = dialogs.UpdateProgress(self, book)
        exit_code = dialog.exec()
        if dialog.save_changes and lib_name is not None:
            new_lib = "Already Read" if dialog.is_finished() else lib_name
            self.home.data = models.update_book(
                self.home.data, book, dialog.updated(), lib_name, new_lib
            )
            self.update_view(lib_name)
            self.home.go_to(new_lib)
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
        self.holder = parent
        self.show_progress = show_progress
        self.show_rating = show_rating
        self.setSizePolicy(CARD_SIZE_POLICY)
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        layout = widgets.QVBoxLayout(self)
        title_layout = widgets.QHBoxLayout()
        title = widgets.QLabel(book.title.title())
        tool_button = widgets.QToolButton(self)
        tool_button.setIcon(QIcon(QPixmap(dialogs.ASSETS["menu_icon"])))
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
            empty_star = QPixmap(dialogs.ASSETS["star_outline"])
            filled_star = QPixmap(dialogs.ASSETS["star_filled"])
            rating_bar = widgets.QWidget(self)
            bar_layout = widgets.QHBoxLayout(rating_bar)
            stars = dialogs.normalise(book.rating, 5, 1)
            for index in range(1, 6):
                label = widgets.QLabel(self)
                label.setPixmap(empty_star if index > stars else filled_star)
                bar_layout.addWidget(label)
            layout.addWidget(rating_bar)
        if self.show_progress:
            bar = widgets.QProgressBar(self)
            bar.setMaximum(book.pages)
            bar.setValue(dialogs.normalise(book.current_page, book.pages))
            layout.addWidget(bar)

    def _setup_menu(self) -> widgets.QMenu:
        menu = widgets.QMenu(self)
        quote_icon = QIcon(QPixmap(dialogs.ASSETS["quote_icon"]))
        quote_action = menu.addAction(quote_icon, "Quote")
        quote_action.triggered.connect(self.quote_book)

        if self.show_rating:
            rating_icon = QIcon(QPixmap(dialogs.ASSETS["star_half"]))
            rating_action = menu.addAction(rating_icon, "Rate")
            rating_action.triggered.connect(self.rate_book)
        if self.show_progress:
            update_icon = QIcon(QPixmap(dialogs.ASSETS["bookmark_icon"]))
            update_action = menu.addAction(update_icon, "Update reading progress")
            update_action.triggered.connect(self.update_progress)
        if self.show_rating or self.show_progress:
            menu.addSeparator()

        edit_icon = QIcon(QPixmap(dialogs.ASSETS["edit_icon"]))
        edit_action = menu.addAction(edit_icon, "Edit")
        edit_action.triggered.connect(self.edit_book)
        change_icon = QIcon(QPixmap(dialogs.ASSETS["shelf_icon"]))
        change_action = menu.addAction(change_icon, "Change Library")
        change_action.triggered.connect(self.change_library)
        delete_icon = QIcon(QPixmap(dialogs.ASSETS["trash_icon"]))
        delete_action = menu.addAction(delete_icon, "Delete")
        delete_action.triggered.connect(self.delete_book)
        return menu

    def change_library(self) -> int:
        return self.holder.change_library(self.book)

    def delete_book(self) -> int:
        return self.holder.delete_book(self.book)

    def edit_book(self) -> int:
        return self.holder.edit_book(self.book)

    def quote_book(self) -> int:
        return self.holder.quote_book(self.book)

    def rate_book(self) -> int:
        return self.holder.rate_book(self.book)

    def update_progress(self) -> int:
        return self.holder.update_progress(self.book)


class SideBar(widgets.QScrollArea):
    def __init__(self, parent: Home) -> None:
        super().__init__(parent)
        self.home: Home = parent
        self.setAlignment(Qt.AlignTop)
        self.setWidgetResizable(True)

        holder = widgets.QWidget(self)
        self.layout_ = widgets.QVBoxLayout(holder)
        self.setWidget(holder)
        self._add_quotes()

    def _add_quotes(self) -> None:
        for quote, book in models.list_quotes(self.home.data):
            card = widgets.QLabel(f"{quote['text']} - <b>{book.author.title()}</b>")
            self.layout_.addWidget(card)
            card.setFrameStyle(widgets.QFrame.StyledPanel)
            card.setSizePolicy(CARD_SIZE_POLICY)
            card.setTextFormat(Qt.TextFormat.RichText)
            card.setWordWrap(True)

    def update_(self) -> None:
        _clear_layout(self.layout_)
        self._add_quotes()


def _clear_layout(layout: widgets.QLayout) -> None:
    while (child := layout.takeAt(0)) is not None:
        widget = child.widget()
        widget.deleteLater()


def run_ui(title: str, data: models.Data) -> tuple[models.Data, int]:
    app = widgets.QApplication()
    window = Home(title, data)
    window.show()
    exit_status = app.exec()
    return window.data, exit_status
