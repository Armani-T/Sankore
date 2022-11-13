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


def find_book(data: Data, target_title: str) -> Optional[Book]:
    for book in data:
        if book.title == target_title:
            return book
    return None


def insert_book(data: Data, new_book: Book) -> Data:
    return (new_book, *data)


def list_quotes(data: Data) -> Iterable[tuple[str, str]]:
    for book in data:
        for quote in book.quotes:
            yield quote, book.author


def update_book(data: Data, old_book: Book, new_book: Book) -> Data:
    return (new_book, *remove_book(data, old_book))


def remove_book(data: Data, target_book: Book) -> Data:
    return tuple(book for book in data if book != target_book)


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
