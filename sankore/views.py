from sqlite3 import Connection

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6 import QtWidgets as widgets

import dialogs
from models import Book

CARD_SIZE_POLICY = widgets.QSizePolicy(
    widgets.QSizePolicy.Minimum, widgets.QSizePolicy.Fixed
)

get_icon = lambda icon_name: QIcon(QPixmap(dialogs.ASSETS[icon_name]))


class Home(widgets.QMainWindow):
    def __init__(self, title: str, connection: Connection) -> None:
        super().__init__()
        self.connection = connection

        QCoreApplication.setApplicationName(title)
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
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO books VALUES (?, ?, ?, ?);", dialog.result())
            self.connection.commit()
            cursor.close()
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
        self.cursor = self.home.connection.cursor()
        self.layout_ = widgets.QGridLayout(self)
        self.layout_.setAlignment(Qt.AlignTop)

    def _populate(self) -> None:
        row, col = 0, 0
        books = sorted(
            self.cursor.execute("SELECT * FROM books;").fetchall(),
            key=lambda b: b[0],
        )
        for (title, author, pages, rating) in books:
            book = Book(title=title, author=author, pages=pages, rating=rating)
            card = Card(self, book)
            self.layout_.addWidget(card, row, col, Qt.AlignBaseline)
            row, col = ((row + 1), 0) if col > 1 else (row, (col + 1))

    def update_view(self) -> None:
        _clear_layout(self.layout_)
        self._populate()

    def delete_book(self, book: Book) -> None:
        dialog = dialogs.AreYouSure(self, book.title)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute("DELETE FROM books WHERE title = ?;", (book.title,))
            self.cursor.connection.commit()
            self.update_view()

    def edit_book(self, book: Book) -> None:
        dialog = dialogs.EditBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            new_title, new_author, new_pages = dialog.result()
            self.cursor.execute(
                "UPDATE books SET title = ?, author = ?, pages = ? WHERE title = ?;",
                (new_title, new_author, new_pages, book.title),
            )
            self.cursor.connection.commit()
            self.update_view()

    def log_completed(self, book: Book) -> None:
        dialog = dialogs.LogRead(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute(
                "INSERT INTO finished_reads VALUES (?, ?, ?);",
                (book.title, *dialog.result()),
            )
            self.cursor.connection.commit()
            self.update_view()

    def quote_book(self, book: Book) -> None:
        dialog = dialogs.QuoteBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute("INSERT INTO quotes VALUES (?, ?);", dialog.result())
            self.cursor.connection.commit()
            self.update_view()
            self.home.update_sidebar()

    def rate_book(self, book: Book) -> None:
        dialog = dialogs.RateBook(self, book)
        dialog.exec()
        if dialog.save_changes:
            self.cursor.execute(
                "UPDATE books SET rating = ? WHERE title = ?;", dialog.result()
            )
            self.cursor.connection.commit()
            self.update_view()

    def start_reading(self, book: Book) -> None:
        self.cursor.execute(
            "INSERT INTO ongoing_reads VALUES (?, ?, ?);",
            (book.title, dialogs.get_today(), 1),
        )
        self.cursor.connection.commit()
        self.update_view()

    def update_progress(self, book: Book) -> None:
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

            self.cursor.connection.commit()
            self.update_view()


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
            bar.setValue(dialogs.normalise(run["page"], book.pages))
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
            stars = dialogs.normalise(book.rating, 5, 1)
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
            update_action.triggered.connect(self.update_progress)
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

    def update_progress(self) -> None:
        self.holder.update_progress(self.book)


class SideBar(widgets.QScrollArea):
    def __init__(self, parent: Home) -> None:
        super().__init__(parent)
        self.home: Home = parent
        self.cursor = self.home.connection.cursor()
        self.setAlignment(Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        holder = widgets.QWidget(self)
        self.layout_ = widgets.QVBoxLayout(holder)
        self.setWidget(holder)
        self.update_()

    def update_(self) -> None:
        _clear_layout(self.layout_)
        self.layout_.addWidget(widgets.QLabel("<h1>Saved Quotes</h1>"))
        quotes = self.cursor.execute("SELECT text_, author FROM quotes;").fetchall()
        for text, author in quotes:
            card = widgets.QLabel(f'"{text}" - <b>{author.title()}</b>')
            card.setFrameStyle(widgets.QFrame.StyledPanel)
            card.setSizePolicy(CARD_SIZE_POLICY)
            card.setTextFormat(Qt.TextFormat.RichText)
            card.setWordWrap(True)
            self.layout_.addWidget(card)


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
