from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6 import QtWidgets as widgets

import dialogs
import models

CARD_SIZE_POLICY = widgets.QSizePolicy(
    widgets.QSizePolicy.Minimum, widgets.QSizePolicy.Fixed
)

get_icon = lambda icon_name: QIcon(QPixmap(dialogs.ASSETS[icon_name]))


class Home(widgets.QMainWindow):
    def __init__(self, title: str, data: models.Data) -> None:
        super().__init__()
        self.data = data

        QCoreApplication.setApplicationName("Sankore")
        self.setWindowIcon(QIcon(QPixmap(dialogs.ASSETS["app_icon"])))
        self.setWindowTitle(title)

        new_menu = self.menuBar().addMenu("New")
        about_menu = self.menuBar().addMenu("About")
        new_book_action = new_menu.addAction("New Book")
        about_action = about_menu.addAction("About")
        new_book_action.triggered.connect(self._new_book)
        about_action.triggered.connect(self._show_about)

        scroll_area = widgets.QScrollArea(self)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards = CardView(self)
        self.cards.update_view()
        scroll_area.setWidget(self.cards)
        scroll_area.setAlignment(Qt.AlignTop)
        scroll_area.setWidgetResizable(True)

        self.sidebar = SideBar(self)

        centre = widgets.QWidget(self)
        self.setCentralWidget(centre)
        centre_layout = widgets.QGridLayout(centre)
        centre_layout.addWidget(scroll_area, 0, 0, 1, 20)
        centre_layout.addWidget(self.sidebar, 0, 21, 1, 5)

    def _new_book(self) -> int:
        dialog = dialogs.NewBook(self)
        exit_code = dialog.exec()
        if dialog.save_changes:
            self.data = models.insert_book(self.data, dialog.new_book())
            self.cards.update_view()
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

    def update_sidebar(self) -> None:
        self.sidebar.update_()


class CardView(widgets.QWidget):
    def __init__(self, parent: Home) -> None:
        super().__init__(parent)
        self.setSizePolicy(widgets.QSizePolicy.Ignored, widgets.QSizePolicy.Fixed)
        self.home: Home = parent
        self.layout_ = widgets.QGridLayout(self)
        self.layout_.setAlignment(Qt.AlignTop)

    def _populate(self) -> None:
        row, col = 0, 0
        for book in self.home.data:
            card = Card(self, book)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def update_view(self) -> None:
        _clear_layout(self.layout_)
        self._populate()

    def delete_book(self, book: models.Book) -> None:
        dialog = dialogs.AreYouSure(self, book.title)
        dialog.exec()
        if dialog.save_changes:
            self.home.data = models.remove_book(self.home.data, book)
            self.update_view()

    def edit_book(self, book: models.Book) -> None:
        dialog = dialogs.EditBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.home.data = models.update_book(self.home.data, book, dialog.updated())
            self.update_view()

    def log_completed(self, book: models.Book) -> None:
        dialog = dialogs.LogRead(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.home.data = models.update_book(self.home.data, book, dialog.updated())
            self.update_view()

    def quote_book(self, book: models.Book) -> None:
        dialog = dialogs.QuoteBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            kwargs = book.to_dict() | {"quotes": (*book.quotes, dialog.quote())}
            new_book = models.Book(**kwargs)  # type: ignore
            self.home.data = models.update_book(self.home.data, book, new_book)
            self.update_view()
            self.home.update_sidebar()

    def rate_book(self, book: models.Book) -> None:
        dialog = dialogs.RateBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.home.data = models.update_book(self.home.data, book, dialog.updated())
            self.update_view()

    def start_reading(self, book: models.Book) -> None:
        new_read = {"start": models.get_today(), "page": 0}
        kwargs = book.to_dict() | {"current_run": new_read}
        new_book = models.Book(**kwargs)  # type: ignore
        self.home.data = models.update_book(self.home.data, book, new_book)
        self.update_view()

    def update_progress(self, book: models.Book) -> None:
        dialog = dialogs.UpdateProgress(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.home.data = models.update_book(self.home.data, book, dialog.updated())
            self.update_view()


class Card(widgets.QFrame):
    def __init__(self, parent: CardView, book: models.Book) -> None:
        super().__init__(parent)
        self.book = book
        self.holder = parent
        self.setSizePolicy(CARD_SIZE_POLICY)
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        layout = widgets.QVBoxLayout(self)
        title_layout = widgets.QHBoxLayout()
        title = widgets.QLabel(f"<b>{book.title.title()}</b>")
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

        if book.current_run is not None:
            bar = widgets.QProgressBar(self)
            bar.setMaximum(book.pages)
            bar.setValue(dialogs.normalise(book.current_run["page"], book.pages))
            layout.addWidget(bar)
        elif not self.book.reads:
            read_status = widgets.QLabel("<i>Never read</i>")
            layout.addWidget(read_status, alignment=Qt.AlignLeft)
        elif (times_read := len(self.book.reads)) > 1:
            read_status = widgets.QLabel(f"<i>Read {times_read} times</i>")
            layout.addWidget(read_status, alignment=Qt.AlignLeft)

        if self.book.reads and self.book.rating:
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

    def _setup_menu(self) -> widgets.QMenu:
        menu = widgets.QMenu(self)
        quote_action = menu.addAction(get_icon("quote_icon"), "Save quote")
        quote_action.triggered.connect(self.quote_book)
        if self.book.current_run is not None:
            update_action = menu.addAction(get_icon("bookmark_icon"), "Update position")
            update_action.triggered.connect(self.update_progress)
        elif self.book.current_run is None:
            start_action = menu.addAction(get_icon("shelf_icon"), "Start reading")
            start_action.triggered.connect(self.start_reading)

        if self.book.rating != 0:
            rating_action = menu.addAction(get_icon("star_half"), "Rate")
            rating_action.triggered.connect(self.rate_book)

        menu.addSeparator()
        log_action = menu.addAction(get_icon("shelf_icon"), "Log completed read")
        log_action.triggered.connect(self.log_completed)
        edit_action = menu.addAction(get_icon("edit_icon"), "Edit")
        edit_action.triggered.connect(self.edit_book)
        delete_action = menu.addAction(get_icon("trash_icon"), "Delete")
        delete_action.triggered.connect(self.delete_book)
        return menu

    def delete_book(self) -> None:
        self.holder.delete_book(self.book)

    def edit_book(self) -> None:
        self.holder.edit_book(self.book)

    def log_completed(self) -> None:
        self.holder.log_completed(self.book)

    def quote_book(self) -> None:
        self.holder.quote_book(self.book)

    def rate_book(self) -> None:
        self.holder.rate_book(self.book)

    def start_reading(self) -> None:
        self.holder.start_reading(self.book)

    def update_progress(self) -> None:
        self.holder.update_progress(self.book)


class SideBar(widgets.QScrollArea):
    def __init__(self, parent: Home) -> None:
        super().__init__(parent)
        self.home: Home = parent
        self.setAlignment(Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        holder = widgets.QWidget(self)
        self.layout_ = widgets.QVBoxLayout(holder)
        self.setWidget(holder)
        self._add_quotes()

    def _add_quotes(self) -> None:
        self.layout_.addWidget(widgets.QLabel("<h1>Saved Quotes</h1>"))
        for quote, author in models.list_quotes(self.home.data):
            card = widgets.QLabel(f'"{quote}" - <b>{author.title()}</b>')
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
