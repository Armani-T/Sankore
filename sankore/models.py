from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, TypedDict
import json

Data = dict[str, "Library"]
Quote = TypedDict("Quote", {"page": Optional[int], "text": str})


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    current_page: int
    rating: int
    quotes: Sequence[Quote] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "author": self.author,
            "pages": self.pages,
            "current_page": self.current_page,
            "rating": self.rating,
            "quotes": self.quotes,
        }


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Library:
    books: Sequence[Book]
    description: str
    page_tracking: bool = False
    can_rate: bool = False


ALL_BOOKS = "All Books"
DEFAULT_DATA: Data = {
    "To Read": Library(books=(), description="Books that I want read in the future."),
    "Already Read": Library(books=(), description="Books that I've finished reading."),
    "Currently Reading": Library(
        books=(),
        description="Books that I'm reading right now.",
        page_tracking=True,
    ),
}


def _prepare_json(json_data: dict[str, Any]) -> Data:
    format_lib = lambda lib_json: Library(
        books=[Book(**book_json) for book_json in lib_json["books"]],
        description=lib_json["description"],
        page_tracking=lib_json["page_tracking"],
    )
    return {
        name: format_lib(library) for name, library in json_data["libraries"].items()
    }


def _prepare_string(data: Data) -> str:
    lib_to_dict = lambda lib: {
        "books": [book.to_dict() for book in lib.books],
        "description": lib.description,
        "page_tracking": lib.page_tracking,
    }
    dict_data = {name: lib_to_dict(library) for name, library in data.items()}
    return json.dumps({"libraries": dict_data})


def get_data(data_file: Path) -> Data:
    try:
        contents = data_file.read_text("utf8")
        data = json.loads(contents)
        return _prepare_json(data)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return DEFAULT_DATA


def save_data(data_file: Path, new_data: Data) -> None:
    string = _prepare_string(new_data)
    data_file.write_text(string, "utf8")


def create_lib(data: Data, name: str, new_lib: Library) -> tuple[int, Data]:
    if name:
        return 0, {name: new_lib, **data}
    return 1, data


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


def list_quotes(data: Data, lib_name: str) -> Iterable[Tuple[Quote, str]]:
    for book in list_books(data, ALL_BOOKS):
        for quote in book.quotes:
            yield (quote, book.title)


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
