from json import dumps, loads
from pathlib import Path
from typing import Iterable, TypedDict

ALL_BOOKS = "All Books"

Data = dict[str, "Library"]


class Book(TypedDict):
    title: str
    author: str
    pages: int
    current_page: int


class Library(TypedDict):
    description: str
    books: list[Book]


def get_data(data_file: Path) -> Data:
    contents = data_file.read_text("utf8")
    json = loads(contents)
    return json["libraries"]


def save_data(data_file: Path, new_data: Data) -> None:
    json_string = dumps({"libraries": new_data})
    data_file.write_text(json_string, "utf8")


def insert_book(data: Data, library: str, new_book: Book) -> None:
    data[library]["books"].append(new_book)


def find_book(data: Data, book_title: str) -> Book:
    for book in list_books(data, ALL_BOOKS):
        if book["title"] == book_title:
            return book
    raise KeyError(f"No book with the title: {book_title}")


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
    replace = lambda book: new_book if book.title == old_title else book
    data[name]["books"] = list(map(replace, data[name]["books"]))
