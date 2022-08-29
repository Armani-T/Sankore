from pathlib import Path
from typing import Iterable, Optional, TypedDict
import json

Data = dict[str, "Library"]

ALL_BOOKS = "All Books"
DEFAULT_LIBRARIES: Data = {
    "To Read": {"description": "Books that I want read in the future.", "books": []},
    "Already Read": {"description": "Books that I've finished reading.", "books": []},
    "Currently Reading": {
        "description": "Books that I'm reading right now.",
        "books": [],
    },
    "Archived": {
        "description": "Books that I stopped reading without finishing.",
        "books": [],
    },
}


class Book(TypedDict):
    title: str
    author: str
    pages: int
    current_page: int


class Library(TypedDict):
    description: str
    books: list[Book]


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


def update_book(data: Data, name: str, old_title: str, new_book: Book) -> None:
    replace = lambda book: new_book if book["title"] == old_title else book
    data[name]["books"] = list(map(replace, data[name]["books"]))
