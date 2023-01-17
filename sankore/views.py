from datetime import datetime
from sqlite3 import Connection, Cursor
from typing import Callable

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6 import QtWidgets as widgets

import dialogs
from models import Book

WidgetBuilder = Callable[[widgets.QWidget, Cursor], widgets.QWidget]

CARD_SIZE_POLICY = widgets.QSizePolicy(
    widgets.QSizePolicy.Minimum, widgets.QSizePolicy.Fixed
)

header = lambda text, level=1: f"<h{level}>{text}</h{level}>"
get_icon = lambda icon_name: QIcon(QPixmap(dialogs.ASSETS[icon_name]))


class Home(widgets.QMainWindow):
    def __init__(self, title: str, connection: Connection) -> None:
        super().__init__()
        self.connection = connection
        self.cursor = connection.cursor()

        QCoreApplication.setApplicationName(title)
        self.setWindowIcon(QIcon(QPixmap(dialogs.ASSETS["app_icon"])))
        self.setWindowTitle(title)

        new_menu = self.menuBar().addMenu("New")
        about_menu = self.menuBar().addMenu("About")
        new_book_action = new_menu.addAction("New Book")
        about_action = about_menu.addAction("About")
        new_book_action.triggered.connect(self.new_book)
        about_action.triggered.connect(self._show_about)

        scroll_area = widgets.QScrollArea(self)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards = CardView(self)
        self.cards.update_view()
        scroll_area.setWidget(self.cards)
        scroll_area.setAlignment(Qt.AlignTop)
        scroll_area.setWidgetResizable(True)

        self.sidebar = self._create_sidebar()

        centre = widgets.QWidget(self)
        self.setCentralWidget(centre)
        centre_layout = widgets.QGridLayout(centre)
        centre_layout.addWidget(scroll_area, 0, 0, 1, 20)
        centre_layout.addWidget(self.sidebar, 0, 21, 1, 5)

    def _create_sidebar(self) -> widgets.QWidget:
        new_cursor = self.connection.cursor()
        base = widgets.QWidget(self)
        base.quotes = QuoteBar(self, new_cursor)
        base.read = ReadingBar(self, new_cursor, self.save_progress)
        base_layout = widgets.QVBoxLayout(base)
        base_layout.addWidget(widgets.QLabel(header("Still Reading", 3)))
        base_layout.addWidget(base.read)
        base_layout.addWidget(widgets.QLabel(header("Recent Quotes", 3)))
        base_layout.addWidget(base.quotes)
        return base

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

    # noinspection PyUnresolvedReferences
    def _update_view(self) -> None:
        self.cards.update_view()
        self.sidebar.read.update_view()
        self.sidebar.quotes.update_view()

    def delete_book(self, book: Book) -> None:
        dialog = dialogs.AreYouSure(self, book.title)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute("DELETE FROM books WHERE title = ?;", (book.title,))
            self.connection.commit()
            self._update_view()

    def edit_book(self, book: Book) -> None:
        dialog = dialogs.EditBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            new_title, new_author, new_pages = dialog.result()
            self.cursor.execute(
                "UPDATE books SET title = ?, author = ?, pages = ? WHERE title = ?;",
                (new_title, new_author, new_pages, book.title),
            )
            self.connection.commit()
            self._update_view()

    def log_completed(self, book: Book) -> None:
        dialog = dialogs.LogRead(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute(
                "INSERT INTO finished_reads VALUES (?, ?, ?);", dialog.result()
            )
            self.connection.commit()
            self._update_view()

    def quote_book(self, book: Book) -> None:
        dialog = dialogs.QuoteBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute("INSERT INTO quotes VALUES (?, ?, ?);", dialog.result())
            self.connection.commit()
            # noinspection PyUnresolvedReferences
            self.sidebar.quotes.update_view()

    def new_book(self) -> None:
        dialog = dialogs.NewBook(self)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute(
                "INSERT INTO books VALUES (?, ?, ?, null);", dialog.result()
            )
            self.connection.commit()
            self._update_view()

    def rate_book(self, book: Book) -> None:
        dialog = dialogs.RateBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute(
                "UPDATE books SET rating = ? WHERE title = ?;", dialog.result()
            )
            self.connection.commit()
            self._update_view()

    def start_reading(self, book: Book) -> None:
        self.cursor.execute(
            "INSERT INTO ongoing_reads VALUES (?, ?, ?);",
            (book.title, dialogs.get_today(), 1),
        )
        self.connection.commit()
        self._update_view()

    def save_progress(self, book: Book) -> None:
        old_progress = book.current_run(self.cursor)
        dialog = dialogs.UpdateProgress(self, book, old_progress["page"])
        dialog.exec()
        if dialog.save_changes:
            if dialog.is_finished():
                self.cursor.execute(
                    "DELETE FROM ongoing_reads WHERE book_title = ?;",
                    (book.title,),
                ).execute(
                    "INSERT INTO finished_reads VALUES (?, ?, ?);",
                    (book.title, old_progress["start"], dialog.end_date()),
                )
            else:
                self.cursor.execute(
                    "UPDATE ongoing_reads SET page = ? WHERE book_title = ?;",
                    (dialog.new_page(), book.title),
                )
            self.connection.commit()
            self._update_view()


class CardView(widgets.QWidget):
    def __init__(self, parent: Home) -> None:
        super().__init__(parent)
        self.setSizePolicy(widgets.QSizePolicy.Ignored, widgets.QSizePolicy.Fixed)
        self.home: Home = parent
        self.cursor = self.home.connection.cursor()
        self.layout_ = widgets.QGridLayout(self)
        self.layout_.setAlignment(Qt.AlignTop)

    def _populate(self) -> None:
        records = sorted(
            self.cursor.execute("SELECT * FROM books;").fetchall(),
            key=lambda b: b[0],
        )
        row, col = 0, 0
        for record in records:
            self.layout_.addWidget(
                Card(self, Book(*record)), row, col, Qt.AlignBaseline
            )
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def update_view(self) -> None:
        _clear_layout(self.layout_)
        self._populate()

    def delete_book(self, book: Book) -> None:
        return self.home.delete_book(book)

    def edit_book(self, book: Book) -> None:
        return self.home.edit_book(book)

    def log_completed(self, book: Book) -> None:
        return self.home.log_completed(book)

    def quote_book(self, book: Book) -> None:
        return self.home.quote_book(book)

    def rate_book(self, book: Book) -> None:
        return self.home.rate_book(book)

    def start_reading(self, book: Book) -> None:
        return self.home.start_reading(book)

    def save_progress(self, book: Book) -> None:
        return self.home.save_progress(book)


class Card(widgets.QFrame):
    def __init__(self, parent: CardView, book: Book) -> None:
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

        if run := book.current_run(self.holder.cursor):
            bar = widgets.QProgressBar(self)
            bar.setMaximum(book.pages)
            bar.setValue(dialogs.moderate(run["page"], book.pages))
            layout.addWidget(bar)
        elif (times_read := len(self.book.reads(self.holder.cursor))) > 1:
            read_status = widgets.QLabel(f"<i>Read {times_read} times</i>")
            layout.addWidget(read_status, alignment=Qt.AlignLeft)
        elif not self.book.reads(self.holder.cursor):
            read_status = widgets.QLabel("<i>Never read</i>")
            layout.addWidget(read_status, alignment=Qt.AlignLeft)

        if self.book.reads and self.book.rating:
            empty_star = QPixmap(dialogs.ASSETS["star_outline"])
            filled_star = QPixmap(dialogs.ASSETS["star_filled"])
            rating_bar = widgets.QWidget(self)
            bar_layout = widgets.QHBoxLayout(rating_bar)
            stars = dialogs.moderate(book.rating, 5, 1)
            for index_ in range(1, 6):
                label = widgets.QLabel(self)
                label.setPixmap(empty_star if index_ > stars else filled_star)
                bar_layout.addWidget(label)
            layout.addWidget(rating_bar)

    def _setup_menu(self) -> widgets.QMenu:
        menu = widgets.QMenu(self)
        quote_action = menu.addAction(get_icon("quote_icon"), "Save quote")
        quote_action.triggered.connect(self.quote_book)
        if self.book.current_run(self.holder.cursor) is not None:
            update_action = menu.addAction(get_icon("bookmark_icon"), "Update position")
            update_action.triggered.connect(self.save_progress)
        else:
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

    def save_progress(self) -> None:
        self.holder.save_progress(self.book)


class QuoteBar(widgets.QScrollArea):
    def __init__(self, parent: widgets.QWidget, cursor: Cursor) -> None:
        super().__init__(parent)
        self.cursor = cursor
        self.setAlignment(Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        holder = widgets.QWidget(self)
        self.layout_ = widgets.QVBoxLayout(holder)
        self.setWidget(holder)
        self.update_view()

    def update_view(self) -> None:
        _clear_layout(self.layout_)
        quotes = self.cursor.execute("SELECT text_, author FROM quotes;").fetchall()
        for text, author in quotes:
            card = widgets.QLabel(f'"{text}" - <b>{author.title()}</b>')
            card.setFrameStyle(widgets.QFrame.StyledPanel)
            card.setSizePolicy(CARD_SIZE_POLICY)
            card.setTextFormat(Qt.TextFormat.RichText)
            card.setWordWrap(True)
            self.layout_.addWidget(card)


class ReadingBar(widgets.QScrollArea):
    def __init__(
        self,
        parent: widgets.QWidget,
        cursor: Cursor,
        save_progress: Callable[[Book], None],
    ) -> None:
        super().__init__(parent)
        self.cursor = cursor
        self.save_progress = save_progress
        self.setAlignment(Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        holder = widgets.QWidget(self)
        self.layout_ = widgets.QVBoxLayout(holder)
        self.setWidget(holder)
        self.update_view()

    def update_view(self) -> None:
        _clear_layout(self.layout_)
        records = sorted(
            self.cursor.execute("SELECT * FROM ongoing_reads;").fetchall(),
            key=lambda pair: datetime.strptime(pair[1], "%d/%m/%Y"),
            reverse=True,
        )
        for title, *_ in records:
            self.cursor.execute("SELECT * FROM books WHERE title = ?;", (title,))
            self.layout_.addWidget(
                SmallCard(
                    self,
                    Book(*self.cursor.fetchone()),
                    self.cursor,
                    self.save_progress,
                )
            )


class SmallCard(widgets.QFrame):
    def __init__(
        self,
        parent: widgets.QWidget,
        book: Book,
        cursor: Cursor,
        save_progress: Callable[[Book], None],
    ) -> None:
        super().__init__(parent)
        self.setSizePolicy(CARD_SIZE_POLICY)
        self.setFrameStyle(widgets.QFrame.StyledPanel)
        self.mousePressEvent = lambda _, book_=book: save_progress(book_)

        layout = widgets.QVBoxLayout(self)
        layout.addWidget(widgets.QLabel(book.title))
        current_page = book.current_run(cursor)["page"]
        # noinspection PyArgumentList
        layout.addWidget(
            widgets.QProgressBar(
                self,
                maximum=book.pages,
                value=dialogs.moderate(current_page, book.pages),
            )
        )


def _clear_layout(layout: widgets.QLayout) -> None:
    while (child := layout.takeAt(0)) is not None:
        widget = child.widget()
        widget.deleteLater()


def run_ui(title: str, connection: Connection) -> int:
    app = widgets.QApplication()
    window = Home(title, connection)
    window.show()
    status = app.exec()
    connection.commit()
    return status
