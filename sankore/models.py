from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, TypedDict
import json

Data = Sequence[Book]
Attempt = TypedDict("Attempt", {"start": Optional[str], "page": int})
Read = TypedDict("Read", {"start": Optional[str], "end": Optional[str]})


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    rating: int
    current: Optional[Attempt] = None
    quotes: Sequence[str] = ()
    runs: Sequence[FullRead] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "current": self.current,
            "rating": self.rating,
            "quotes": self.quotes,
            "runs": self.runs,
        }


def get_data(data_file: Path) -> Data:
    try:
        contents = data_file.read_text("utf8")
        full_json = json.loads(contents)
        return tuple(
            Book(**book_json)
            for book_json in full_json.get("books", ())
        )
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return ()


def save_data(data_file: Path, new_data: Data) -> None:
    string = json.dumps({"books": [book.to_dict() for book in new_data]})
    data_file.write_text(string, "utf8")


def create_lib(data: Data, name: str, new_lib: Library) -> tuple[int, Data]:
    if name:
        return 0, {name: new_lib, **data}
    return 1, data


def find_book(data: Data, target_title: str) -> Optional[Book]:
    for book in list_books(data, ALL_BOOKS):
        if book.title == target_title:
            return book
    return None


def find_library(data: Data, book: Book) -> Optional[str]:
    for lib_name in list_libraries(data, False):
        if book in data[lib_name].books:
            return lib_name
    return None


def insert_book(data: Data, lib_name: str, new_book: Book) -> Data:
    old_lib = data[lib_name]
    new_lib = Library(
        books=(*old_lib.books, new_book),
        description=old_lib.description,
        page_tracking=old_lib.page_tracking,
    )
    return {**data, lib_name: new_lib}


def list_books(data: Data, lib_name: str) -> Iterable[Book]:
    if lib_name == ALL_BOOKS:
        return chain(*[library.books for library in data.values()])
    if lib_name in data:
        return data[lib_name].books
    return ()


def list_libraries(data: Data, all_: bool = True) -> Iterable[str]:
    if all_:
        yield ALL_BOOKS
    yield from data.keys()


def list_quotes(data: Data, lib_name: str = ALL_BOOKS) -> Iterable[tuple[str, str]]:
    for book in list_books(data, lib_name):
        for quote in book.quotes:
            yield quote, book.author


def update_book(
    data: Data,
    old_book: Book,
    new_book: Book,
    old_lib: str,
    new_lib: Optional[str] = None,
) -> Data:
    new_lib = new_lib or old_lib
    data = remove_book(data, old_book, old_lib)
    return insert_book(data, new_lib, new_book)


def remove_book(data: Data, target_book: Book, lib_name: str) -> Data:
    old_lib = data[lib_name]
    new_library = Library(
        books=[book for book in old_lib.books if book != target_book],
        description=old_lib.description,
        page_tracking=old_lib.page_tracking,
    )
    return {**data, lib_name: new_library}
