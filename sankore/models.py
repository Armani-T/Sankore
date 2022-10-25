from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, TypedDict
import json

get_today = lambda: date.today().strftime("%d/%m/%Y")

Data = Sequence["Book"]
Run = TypedDict("Run", {"start": Optional[str], "page": int})
Read = TypedDict("Read", {"start": Optional[str], "end": Optional[str]})


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    rating: int
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


def get_data(data_file: Path) -> Data:
    try:
        contents = data_file.read_text("utf8")
        full_json = json.loads(contents)
        return tuple(Book(**book_json) for book_json in full_json.get("books", ()))
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return ()


def save_data(data_file: Path, new_data: Data) -> None:
    string = json.dumps({"books": [book.to_dict() for book in new_data]})
    data_file.write_text(string, "utf8")


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
