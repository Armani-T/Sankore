from collections.abc import Collection, Iterable
from dataclasses import dataclass
from itertools import chain
from shelve import Shelf, open as open_shelf

ALL_BOOKS = "All Books"


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

    def __getitem__(self, title):
        for book in self.books:
            if book.title == title:
                return book
        raise KeyError(f'There is no book called "{title}" in this library.')


def get_db(db_file: str) -> Shelf:
    db = open_shelf(db_file, flag="c", protocol=4)
    db.setdefault("To Read", Library("The books that I haven't read yet.", ()))
    db.setdefault("Already Read", Library("The books I intend to read later.", ()))
    db.setdefault("Reading Now", Library("The books I'm reading right now.", ()))
    db.setdefault(
        "Archived",
        Library("The books I started reading but stopped before finishing.", ()),
    )
    return db


def insert_book(db: Shelf, library: str, new_book: Book) -> None:
    db[library] = db[library].insert(new_book)


def find_book(db: Shelf, book_title: str) -> Book:
    full_list = list_all_books(db)
    return full_list[book_title]


def list_all_books(db: Shelf) -> Library:
    result = sum(db.values(), Library())
    result.description = "All the books recorded in the library."
    return result


def list_books(db: Shelf, name: str) -> Library:
    return list_all_books(db) if name == ALL_BOOKS else db[name]


def list_libraries(db: Shelf, all_: bool = True) -> Iterable[str]:
    if all_:
        yield ALL_BOOKS
    yield from db.keys()


def switch_library(db: Shelf, old_name: str, new_name: str, book: Book) -> None:
    old_lib = db[old_name]
    db[old_lib] = Library(
        old_lib.description,
        [item for item in old_lib.books if item != book],
    )
    return insert_book(db, new_name, book)


def update_book(db: Shelf, name: str, old_title: str, new_book: Book) -> None:
    library = db[name]
    db[name] = Library(
        library.description,
        [new_book if book.title == old_title else book for book in db[name]],
    )
