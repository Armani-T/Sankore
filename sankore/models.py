from dataclasses import dataclass
from datetime import date
from pathlib import Path
from sqlite3 import connect, Cursor
from typing import Any, Iterable, Optional, Sequence, TypedDict

INIT_DB_SCRIPT = Path(__file__) / "../../assets/init.sql"

Data = Sequence["Book"]
Run = TypedDict("Run", {"start": Optional[str], "page": int})
Read = TypedDict("Read", {"start": Optional[str], "end": Optional[str]})

get_today = lambda: date.today().strftime("%d/%m/%Y")


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    rating: int = 0
    current_run: Optional[Run] = None
    quotes: Sequence[str] = ()
    reads: Sequence[Read] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "current_run": self.current_run,
            "rating": self.rating,
            "quotes": self.quotes,
            "reads": self.reads,
        }

    def to_tuple(self) -> tuple[str, str, int, int]:
        return (self.title, self.author, self.pages, self.rating)


def get_cursor(db_file: Path) -> Cursor:
    initialise = not db_file.exists()
    db_file.touch(exist_ok=True)
    connection = connect(str(db_file))
    if initialise:
        script_text = INIT_DB_SCRIPT.read_text("utf8")
        init_cursor = connection.cursor()
        init_cursor.executescript(script_text)
        connection.commit()
        init_cursor.close()
    return connection.cursor()


def find_book(cursor: Cursor, target_title: str) -> Optional[Book]:
    cursor.execute("SELECT * FROM books WHERE title = ?", (target_title,))
    book_info = cursor.fetchone()
    return None if book_info is None else Book(*book_info)


def insert_book(cursor: Cursor, new_book: Book) -> None:
    cursor.execute("INSERT INTO books VALUES (?, ?, ?, ?)", new_book.to_tuple())
    cursor.connection.commit()


def list_quotes(cursor: Cursor) -> Iterable[tuple[str, str]]:
    cursor.execute("SELECT (text_, author) FROM quotes")
    quote: Optional[tuple[str, str]]
    quote = cursor.fetchone()
    while quote is not None:
        yield quote
        quote = cursor.fetchone()


def remove_book(cursor: Cursor, book: Book) -> Data:
    cursor.execute("DELETE FROM books WHERE title = ?", (book.title,))
    cursor.connection.commit()


def update_book(cursor: Cursor, old_book: Book, new_book: Book) -> None:
    cursor.execute(
        "UPDATE books SET title = ?, author = ?, pages = ? WHERE title = ?",
        (new_book.title, new_book.author, new_book.pages, old_book.title),
    )
    cursor.connection.commit()
