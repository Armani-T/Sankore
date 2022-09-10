from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence
import json

Data = dict[str, "Library"]

ALL_BOOKS = "All Books"
DEFAULT_LIBRARIES: Data = {
    "To Read": {
        "books": [],
        "description": "Books that I want read in the future.",
        "page_tracking": False,
    },
    "Already Read": {
        "books": [],
        "description": "Books that I've finished reading.",
        "page_tracking": False,
    },
    "Currently Reading": {
        "books": [],
        "description": "Books that I'm reading right now.",
        "page_tracking": True,
    },
}


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Book:
    title: str
    author: str
    pages: int
    current_page: int


@dataclass(frozen=True, kw_only=True, slots=True, unsafe_hash=True)
class Library:
    books: Sequence[Book]
    description: str
    page_tracking: bool = False


def _prepare_json(json: dict[str, Any]) -> Data:
    format_lib = lambda lib_json: Library(
        books=map(lambda book_json: Book(**book_json), lib_json),
        description=lib_json["description"],
        page_tracking=lib_json["page_tracking"],
    )
    return {name: format_lib(library) for name, library in json["libraries"].items()}


def _prepare_string(data: Data) -> dict[str, Any]:
    lib_to_dict = lambda lib: {**lib.asdict(), "books": map(Book.asdict, lib.books)}
    dict_data = {name: lib_to_dict(library) for name, library in data.items()}
    return json.dumps({"libraries": dict_data})


def get_data(data_file: Path) -> Data:
    try:
        contents = data_file.read_text("utf8")
        data = json.loads(contents)
        return _prepare_json(data)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return DEFAULT_LIBRARIES


def save_data(data_file: Path, new_data: Data) -> None:
    string = _prepare_string(new_data)
    data_file.write_text(string, "utf8")


def create_lib(data: Data, name: str, new_lib: Library) -> tuple[int, Data]:
    if name:
        return 0, {name: new_lib, **data}
    return 1, data


def find_library(data: Data, book: Book) -> Optional[str]:
    for name in list_libraries(data, False):
        if book in data[name]["books"]:
            return name
    return None


def insert_book(data: Data, library: str, new_book: Book) -> Data:
    old_books = data[library]["books"]
    new_library = {**data[library], "books": (*old_books, new_book)}
    return {**data, library: new_library}


def list_books(data: Data, lib_name: str) -> Iterable[Book]:
    if lib_name == ALL_BOOKS:
        return chain(map(lambda library: library["books"], data.values()))
    if lib_name in data:
        return data[lib_name]["books"]
    return ()


def list_libraries(data: Data, all_: bool = True) -> Iterable[str]:
    if all_:
        yield ALL_BOOKS
    yield from data.keys()


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


def remove_book(data: Data, target_book: Book, library: str) -> Data:
    new_books = [book for book in data[library]["books"] if book != target_book]
    new_library = {**data[library], "books": new_books}
    return {**data, library: new_library}
