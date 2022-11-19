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

    def current_run(self, cursor: Cursor) -> Optional[Run]:
        run_info = cursor.execute(
            "SELECT (start, page) FROM ongoing_reads WHERE title = ?",
            (self.title,),
        ).fetchone()
        return (
            {"start": run_info[0], "page": run_info[1]}
            if run_info is not None
            else None
        )

    def reads(self, cursor: Cursor) -> Sequence[Read]:
        cursor.execute(
            "SELECT (start, end_) FROM finished_reads WHERE book_title = ?",
            (self.title,),
        )
        return [{"start": line[0], "end": line[1]} for line in cursor.fetchall()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "rating": self.rating,
        }

    def to_tuple(self) -> tuple[str, str, int, int]:
        return (self.title, self.author, self.pages, self.rating)


def find_book(cursor: Cursor, target_title: str) -> Optional[Book]:
    cursor.execute("SELECT * FROM books WHERE title = ?", (target_title,))
    book_info = cursor.fetchone()
    if book_info is not None:
        title, author, pages, rating = book_info
        return Book(title=title, author=author, pages=pages, rating=rating)
    return None


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


def remove_book(cursor: Cursor, book: Book) -> None:
    cursor.execute("DELETE FROM books WHERE title = ?", (book.title,))
    cursor.connection.commit()


def update_book(cursor: Cursor, old_book: Book, new_book: Book) -> None:
    cursor.execute(
        "UPDATE books SET title = ?, author = ?, pages = ? WHERE title = ?",
        (new_book.title, new_book.author, new_book.pages, old_book.title),
    )
    cursor.connection.commit()
