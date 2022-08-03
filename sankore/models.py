from collections.abc import Collection
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from shelve import open as open_shelf
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

    def insert(self, book: Book):
        return Library(self.description, (book, *self.books))

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
    db = open_shelf(db_file, flag="c", protocol=4)
    db.setdefault(Library("", ()))
    return db


def create_book(db: Database, name: str, new_book: Book) -> None:
    db[name] = db[name].insert(new_book)


def change_library(db: Database, old_lib: str, new_lib: str, book: Book) -> None:
    db[old_lib] = tuple(item for item in get_books(old_lib) if item != book)
    create_book(new_lib, book)


def get_book(db: Database, title: str) -> Book:
    for book in get_books(db):
        if book.title == title:
            return book
    raise ValueError(f'No book with title "{title}" was found.')


def get_books(db: Database, name: str) -> Library:
    return sum(db.values(), Library()) if name == ALL_BOOKS else db[name]


def get_libraries(db: Database, all_: bool = True) -> Collection[str]:
    names = list(db.keys())
    if all_:
        names.insert(0, ALL_BOOKS)
    return names


def update_book(db: Database, name: str, old_title: str, new_book: Book) -> None:
    db[name] = tuple(new_book if book.title == old_title else book for book in db[name])
