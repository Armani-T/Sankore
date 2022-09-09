from pathlib import Path
from typing import Iterable, Optional, Sequence, TypedDict
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


class Book(TypedDict):
    title: str
    author: str
    pages: int
    current_page: int


class Library(TypedDict):
    books: Sequence[Book]
    description: str
    page_tracking: bool


def get_data(data_file: Path) -> Data:
    try:
        contents = data_file.read_text("utf8")
        data = json.loads(contents)
        return data["libraries"]
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return DEFAULT_LIBRARIES


def save_data(data_file: Path, new_data: Data) -> None:
    string = json.dumps({"libraries": new_data})
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


def insert_book(data: Data, library: str, new_book: Book) -> int:
    data[library]["books"].append(new_book)
    return 0


def list_books(data: Data, name: str) -> list[Book]:
    if name == ALL_BOOKS:
        book_lists = map(lambda library: library["books"], data.values())
        return list(sum(book_lists, []))
    return data[name]["books"]


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
) -> None:
    new_lib = new_lib or old_lib
    data[old_lib]["books"].remove(old_book)
    data[new_lib]["books"].append(new_book)


def delete_book(data: Data, book: Book, library: str) -> None:
    data[library]["books"].remove(book)
