from collections.abc import Collection
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from shelve import open as shelve_open
from typing import Mapping, MutableMapping


@dataclass
class Book:
    title: str
    author: str
    pages: int
    current_page: int = 0

    def __hash__(self):
        return hash(self.title)


@dataclass
class Library(Collection[Book]):
    description: str = ""
    books: Collection[Book] = ()

    def __add__(self, other: "Library") -> "Library":
        return Library(self.description, tuple(chain(self.books, other.books)))

    def __contains__(self, book):
        return book in self.books

    def __iter__(self):
        return iter(self.books)

    def __len__(self):
        return len(self.books)


Database = MutableMapping[str, "Library"]

ALL_BOOKS = "All Books"
DEFAULT_LIBRARIES: Mapping[str, str] = {
    "To Read": "The books that I haven't read yet but intend to.",
    "Done Reading": "The books I intend to read later.",
    "Reading Now": "The books I am reading right now.",
    "Archived": "The books I started but stopped reading.",
}


def get_db(db_file: Path) -> Database:
    open_flag = "w" if db_file.exists() else "n"
    db = shelve_open(db_file, flag=open_flag, protocol=4)
    for library in DEFAULT_LIBRARIES:
        if library not in db:
            db[library] = Library(DEFAULT_LIBRARIES[library], ())
    return db


def create_book(lib_name: str, new_book: Book) -> None:
    LIBRARIES[lib_name] = (*get_books(lib_name), new_book)


def change_library(old_lib: str, new_lib: str, book: Book) -> None:
    LIBRARIES[old_lib] = tuple(item for item in get_books(old_lib) if item != book)
    create_book(new_lib, book)


def get_book(title: str) -> Book:
    for book in get_books(ALL_BOOKS):
        if book.title == title:
            return book
    raise ValueError(f'No book with title "{title}" was found.')


def get_books(name) -> Library:
    return sum(LIBRARIES.values(), Library()) if name == ALL_BOOKS else LIBRARIES[name]


def get_libraries(all_: bool = True) -> Collection[str]:
    names = list(LIBRARIES.keys())
    if all_:
        names.insert(0, ALL_BOOKS)
    return names


def update_book(lib_name: str, old_title: str, new_book: Book) -> None:
    LIBRARIES[lib_name] = tuple(
        new_book if book.title == old_title else book for book in LIBRARIES[lib_name]
    )
